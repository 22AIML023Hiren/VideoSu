// Enhanced with error handling and additional animations
try {
    document.addEventListener('DOMContentLoaded', function() {
        // 1. Card Animation with Intersection Observer (better performance)
        const animateCards = () => {
            const cards = document.querySelectorAll('.card');
            
            // Modern approach with Intersection Observer
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry, index) => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '0';
                        entry.target.style.transform = 'translateY(20px)';
                        entry.target.style.transition = `all 0.6s ease ${index * 0.15}s`;
                        
                        setTimeout(() => {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateY(0)';
                        }, 50);
                        
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });

            cards.forEach(card => {
                observer.observe(card);
            });
        };

        // 2. Enhanced Button Interactions
        const enhanceButtons = () => {
            const buttons = document.querySelectorAll('.stButton>button, .download-button');
            
            buttons.forEach(button => {
                // Cursor effect
                button.style.cursor = 'pointer';
                
                // Click animation
                button.addEventListener('click', () => {
                    button.style.transform = 'scale(0.98)';
                    setTimeout(() => {
                        button.style.transform = 'scale(1)';
                    }, 200);
                });
                
                // Hover effect
                button.addEventListener('mouseenter', () => {
                    button.style.filter = 'brightness(1.05)';
                    button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.35)';
                });
                
                button.addEventListener('mouseleave', () => {
                    button.style.filter = 'brightness(1)';
                    button.style.boxShadow = '0 6px 12px rgba(102, 126, 234, 0.3)';
                });
            });
        };

        // 3. Smooth Scroll for Errors
        const setupErrorHandling = () => {
            const errorElements = document.querySelectorAll('.stAlert');
            errorElements.forEach(el => {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            });
        };

        // Initialize all features
        animateCards();
        enhanceButtons();
        setupErrorHandling();

        // 4. Progress Bar Animation (optional)
        const progressBars = document.querySelectorAll('.stProgress > div > div > div');
        progressBars.forEach(bar => {
            bar.style.transition = 'width 0.5s cubic-bezier(0.65, 0, 0.35, 1)';
        });
    });
} catch (error) {
    console.error('Error in custom JavaScript:', error);
}