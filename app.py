from flask import Flask, request, render_template, redirect, url_for, session, flash
import pdfplumber
import re
import spacy
from keybert import KeyBERT
from transformers import pipeline, T5Tokenizer


app = Flask(__name__)

# Load NLP models
nlp = spacy.load("en_core_web_sm")
kw_model = KeyBERT()

# Initialize Valhalla T5 model for question generation
qg_pipeline = pipeline("text2text-generation", model="valhalla/t5-small-qg-prepend")
tokenizer = T5Tokenizer.from_pretrained("valhalla/t5-small-qg-prepend")

# Initialize a question-answering model
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

def extract_clean_text(pdf_file):
    text_chunks = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            raw_text = page.extract_text()
            if raw_text:
                clean_text = "\n".join(
                    line for line in raw_text.split("\n") if len(line.strip()) > 10
                )
                text_chunks.append(clean_text)
    return text_chunks

def split_by_sections(text):
    sections = re.split(r"\n[A-Z ]{3,}\n", text)
    return sections

def extract_relevant_sentences(text):
    doc = nlp(text)
    sentences = [
        sent.text
        for sent in doc.sents
        if any(keyword in sent.text.lower() for keyword in ["is", "steps", "includes", "defined"])
    ]
    return sentences

def segment_by_topics(text_chunks):
    segmented_chunks = {}
    for i, chunk in enumerate(text_chunks):
        keywords = kw_model.extract_keywords(chunk, keyphrase_ngram_range=(1, 2), stop_words='english')
        top_keyword = keywords[0][0] if keywords else f"Chunk_{i+1}"
        segmented_chunks[top_keyword] = chunk
    return segmented_chunks

def truncate_text(text, tokenizer, max_length):
    tokens = tokenizer.encode(text, truncation=True, max_length=max_length)
    return tokenizer.decode(tokens, skip_special_tokens=True)

def generate_questions_with_topic(chunks, topics, qg_pipeline, tokenizer):
    questions = []
    for chunk, topic in zip(chunks, topics):
        input_text = f"context: {topic} {chunk}"
        truncated_input = truncate_text(input_text, tokenizer, max_length=512)
        # Generate questions without sampling
        outputs = qg_pipeline(
            truncated_input,
            max_length=64,
            num_return_sequences=1,
        )
        for output in outputs:
            question = output['generated_text']
            questions.append(question)
    return questions

def process_pdf(pdf_file):
    text_chunks = extract_clean_text(pdf_file)
    structured_data = {}
    for i, chunk in enumerate(text_chunks):
        sections = split_by_sections(chunk)
        for j, section in enumerate(sections):
            relevant_sentences = extract_relevant_sentences(section)
            if relevant_sentences:
                segmented = segment_by_topics(relevant_sentences)
                structured_data.update(segmented)
    return structured_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            pdf_file = request.files['file']
            processed_data = process_pdf(pdf_file)
            chunks = list(processed_data.values())
            topics = list(processed_data.keys())
            questions = generate_questions_with_topic(chunks, topics, qg_pipeline, tokenizer)
            
            qa_results = []
            for chunk, question in zip(chunks, questions):
                answer = qa_pipeline(question=question, context=chunk)
                qa_results.append((question, answer['answer'], answer['score']))
            
            qa_results.sort(key=lambda x: x[2], reverse=True)
            top_5_results = qa_results[:5]
            
            session['flashcards'] = top_5_results
            return redirect(url_for('show_flashcards'))
        except Exception as e:
            flash(str(e))
            return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/flashcards')
def show_flashcards():
    flashcards = session.get('flashcards', [])
    if not flashcards:
        flash('No flashcards available. Please upload a PDF first.')
        return redirect(url_for('index'))
    return render_template('flashcards.html', flashcards=flashcards)

if __name__ == '__main__':
    app.run(debug=True)