let currentCardIndex = 0;

document.addEventListener('DOMContentLoaded', (event) => {
    showCard(currentCardIndex);
    updateButtonStates();
});

function flipCard(card) {
    card.classList.toggle('flipped');
}

function showCard(index) {
    const flashcards = document.querySelectorAll('.flashcard');
    flashcards.forEach((card, i) => {
        card.style.display = i === index ? 'block' : 'none';
    });
    updateButtonStates();
}

function nextCard() {
    const flashcards = document.querySelectorAll('.flashcard');
    if (flashcards.length > 0 && currentCardIndex < flashcards.length - 1) {
        flashcards[currentCardIndex].classList.remove('flipped');
        currentCardIndex++;
        showCard(currentCardIndex);
    }
}

function previousCard() {
    const flashcards = document.querySelectorAll('.flashcard');
    if (flashcards.length > 0 && currentCardIndex > 0) {
        flashcards[currentCardIndex].classList.remove('flipped');
        currentCardIndex--;
        showCard(currentCardIndex);
    }
}

function updateButtonStates() {
    const flashcards = document.querySelectorAll('.flashcard');
    const nextButton = document.querySelector('#nextButton');
    const prevButton = document.querySelector('#prevButton');

    if (currentCardIndex === 0) {
        prevButton.disabled = true;
    } else {
        prevButton.disabled = false;
    }

    if (currentCardIndex === flashcards.length - 1) {
        nextButton.disabled = true;
    } else {
        nextButton.disabled = false;
    }
}