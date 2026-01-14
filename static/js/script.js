document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('.login-form');
    const inputs = document.querySelectorAll('input');

    // Simple interaction effect for inputs
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', () => {
            input.parentElement.classList.remove('focused');
        });
    });

    // Handle form submission
    // loginForm.addEventListener('submit', (e) => {
    //     e.preventDefault();

    //     const btn = document.querySelector('.submit-btn');
    //     const originalText = btn.textContent;

    //     // Simulate loading state
    //     btn.textContent = 'Connexion en cours...';
    //     btn.style.opacity = '0.9';
    //     btn.disabled = true;

    //     // Simulate API call delay
    //     setTimeout(() => {
    //         // Here you would typically handle the login logic
    //         console.log('Login attempt for:', document.getElementById('username').value);

    //         // For now, just reset
    //         btn.textContent = originalText;
    //         btn.style.opacity = '1';
    //         btn.disabled = false;

    //         // Redirect to dashboard
    //         window.location.href = 'dashboard.php';
    //     }, 1500);
    // });
});
