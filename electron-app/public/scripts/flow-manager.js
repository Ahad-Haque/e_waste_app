// public/scripts/flow-manager.js
class FlowManager {
  constructor() {
    this.currentFlow = 'ewaste-selection';
    this.selectedBox = '';
    this.selectedRating = 0;
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    // Waste selection buttons
    document.querySelectorAll('.waste-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.selectedBox = e.target.dataset.box;
        this.showBoxInstruction();
      });
    });

    // Yes/No buttons for learning
    document.getElementById('learn-yes').addEventListener('click', () => {
      this.showGameState();
    });

    document.getElementById('learn-no').addEventListener('click', () => {
      this.showFeedbackState();
    });

    // Feedback screen button
    document.getElementById('feedback-screen-btn').addEventListener('click', () => {
      this.showFeedbackState();
    });

    // Star rating
    document.querySelectorAll('.star').forEach(star => {
      star.addEventListener('click', (e) => {
        this.setRating(parseInt(e.target.dataset.rating));
      });
    });

    // Submit rating
    document.getElementById('submit-rating').addEventListener('click', () => {
      this.submitRating();
    });

    // Photo Yes/No
    document.getElementById('photo-yes').addEventListener('click', () => {
      this.startCountdown();
    });

    document.getElementById('photo-no').addEventListener('click', () => {
      this.endFlow();
    });
  }

  showState(stateId) {
    // Hide all states
    document.querySelectorAll('.flow-state').forEach(state => {
      state.classList.add('hidden');
    });
    
    // Show selected state
    document.getElementById(stateId).classList.remove('hidden');
    this.currentFlow = stateId;
  }

  showBoxInstruction() {
    document.getElementById('box-number').textContent = this.selectedBox;
    this.showState('box-instruction');
    
    // Simulate user going to box and returning
    setTimeout(() => {
      this.showThankYou();
    }, 5000);
  }

  showThankYou() {
    this.showState('thank-you');
    
    // Show learn more after 2 seconds
    setTimeout(() => {
      this.showState('learn-more');
    }, 2000);
  }

  showGameState() {
    this.showState('game-state');
    // Initialize game here if needed
    this.initializeFlappyBird();
  }

  showFeedbackState() {
    this.showState('feedback-state');
  }

  setRating(rating) {
    this.selectedRating = rating;
    
    // Update star display
    document.querySelectorAll('.star').forEach((star, index) => {
      if (index < rating) {
        star.classList.add('active');
      } else {
        star.classList.remove('active');
      }
    });
  }

  submitRating() {
    if (this.selectedRating === 0) {
      alert('Please select a rating');
      return;
    }

    // Save rating to database (implement later)
    console.log('Rating submitted:', this.selectedRating);

    if (this.selectedRating === 5) {
      this.showPhotoState();
    } else {
      this.endFlow();
    }
  }

  showPhotoState() {
    this.showState('photo-state');
    // Play "Thank you for giving us 5 star" audio here
  }

  startCountdown() {
    this.showState('countdown-state');
    let count = 3;
    const countdownElement = document.getElementById('countdown-timer');
    
    const interval = setInterval(() => {
      countdownElement.textContent = count;
      count--;
      
      if (count < 0) {
        clearInterval(interval);
        this.takePhoto();
      }
    }, 1000);
  }

  takePhoto() {
    // Implement photo capture
    console.log('Photo taken!');
    this.endFlow();
  }

  endFlow() {
    // Reset to initial state
    this.selectedRating = 0;
    this.selectedBox = '';
    this.showState('ewaste-selection');
  }

  initializeFlappyBird() {
    // Placeholder for game implementation
    const canvas = document.getElementById('game-canvas');
    const ctx = canvas.getContext('2d');
    
    // Simple game background
    ctx.fillStyle = '#87ceeb';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#000';
    ctx.font = '24px Arial';
    ctx.fillText('Flappy Bird Game', 50, 200);
    ctx.fillText('Coming Soon...', 80, 230);
  }
}

// Initialize flow manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.flowManager = new FlowManager();
});