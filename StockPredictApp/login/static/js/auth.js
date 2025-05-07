document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form-element');
    const registerForm = document.getElementById('register-form-element');
    const loginMessage = document.getElementById('login-message');
    const registerMessage = document.getElementById('register-message');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();
                if (data.success) {
                    // Redirect to index.html with session details
                    window.location.href = `/index.html?session_token=${data.session_token}&username=${data.username}&expiry=${data.expiry}`;
                } else {
                    loginMessage.textContent = data.error || 'Login failed';
                    loginMessage.style.color = 'red';
                }
            } catch (error) {
                loginMessage.textContent = 'An error occurred. Please try again.';
                loginMessage.style.color = 'red';
                console.error('Login error:', error);
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('register-username').value;
            const password = document.getElementById('register-password').value;

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();
                if (data.success) {
                    // Redirect to index.html with session details
                    window.location.href = `/index.html?session_token=${data.session_token}&username=${data.username}&expiry=${data.expiry}`;
                } else {
                    registerMessage.textContent = data.error || 'Registration failed';
                    registerMessage.style.color = 'red';
                }
            } catch (error) {
                registerMessage.textContent = 'An error occurred. Please try again.';
                registerMessage.style.color = 'red';
                console.error('Registration error:', error);
            }
        });
    }
});