// Global Variables
let currentUser = null;
let currentQuiz = null;
let currentQuestionIndex = 0;
let userAnswers = [];
let quizStartTime = null;
let userStats = {
    totalQuizzes: 0,
    totalScore: 0,
    pdfsProcessed: 0,
    studyStreak: 0
};

// App Initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 ScholarQuiz App Starting...');
    initializeApp();
    setupEventListeners();
    checkExistingUser();
});

function initializeApp() {
    console.log('✅ App initialized successfully!');
    showNotification('Welcome to ScholarQuiz!', 'info');
}
function setupEventListeners() {
    console.log('🎯 Setting up event listeners...');
    
    // Navigation tabs
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const sectionId = this.getAttribute('data-section');
            if (sectionId) {
                showSection(sectionId, this);
            }
        });
    });

    // Section links (login/signup switches)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('section-link')) {
            e.preventDefault();
            const targetSection = e.target.getAttribute('data-target');
            if (targetSection) {
                showSection(targetSection);
            }
        }
        
        if (e.target.classList.contains('section-btn')) {
            e.preventDefault();
            const targetSection = e.target.getAttribute('data-target');
            if (targetSection) {
                showSection(targetSection);
            }
        }
    });

    // Form submissions
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }

    console.log('✅ Event listeners set up successfully!');
}

function checkExistingUser() {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        loadUserStats();
        showAuthenticatedTabs();
        showSection('dashboard');
        showNotification(`Welcome back, ${currentUser.name}!`, 'success');
    }
}
// Navigation Functions
function showSection(sectionId, clickedElement = null) {
    console.log(`📍 Switching to section: ${sectionId}`);
    
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => section.classList.remove('active'));
    
    // Remove active class from all tabs
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Show selected section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Add active class to clicked tab or find corresponding tab
    if (clickedElement) {
        clickedElement.classList.add('active');
    } else {
        const targetTab = document.querySelector(`[data-section="${sectionId}"]`);
        if (targetTab) {
            targetTab.classList.add('active');
        }
    }
}

// Authentication Functions
function handleLogin(event) {
    event.preventDefault();
    console.log('🔐 Processing login...');
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        showNotification('Please fill in all fields.', 'error');
        return;
    }
    
    if (password.length < 6) {
        showNotification('Password must be at least 6 characters long.', 'error');
        return;
    }
    
    // Create user session (in real app, this would validate with server)
    currentUser = {
        email: email,
        name: email.split('@')[0],
        fullName: email.split('@')[0],
        loginTime: new Date()
    };
    
    // Store user in localStorage
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    // Load user stats
    loadUserStats();
    
    // Show authenticated tabs
    showAuthenticatedTabs();
    
    // Redirect to dashboard
    showSection('dashboard');
    
    // Clear form
    document.getElementById('loginForm').reset();
    
    showNotification(`Welcome back, ${currentUser.name}!`, 'success');
    console.log('✅ Login successful!');
}

function handleSignup(event) {
    event.preventDefault();
    console.log('📝 Processing signup...');
    
    const firstName = document.getElementById('firstName').value;
    const lastName = document.getElementById('lastName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Validation
    if (!firstName || !lastName || !email || !password) {
        showNotification('Please fill in all required fields.', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showNotification('Passwords do not match.', 'error');
        return;
    }
    
    if (password.length < 6) {
        showNotification('Password must be at least 6 characters long.', 'error');
        return;
    }
    
    // Create new user
    currentUser = {
        firstName: firstName,
        lastName: lastName,
        email: email,
        name: `${firstName} ${lastName}`,
        fullName: `${firstName} ${lastName}`,
        signupTime: new Date()
    };
    
    // Store user in localStorage
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    // Initialize user stats
    initializeUserStats();
    
    // Show authenticated tabs
    showAuthenticatedTabs();
    
    // Redirect to dashboard
    showSection('dashboard');
    
    // Clear form
    document.getElementById('signupForm').reset();
    
    showNotification(`Account created successfully! Welcome ${currentUser.name}!`, 'success');
    console.log('✅ Signup successful!');
}

function showAuthenticatedTabs() {
    console.log('👀 Showing authenticated tabs...');
    document.getElementById('dashboardTab').style.display = 'block';
    document.getElementById('uploadTab').style.display = 'block';
    document.getElementById('quizTab').style.display = 'block';
    document.getElementById('crudTab').style.display = 'block';
}
// User Stats Functions
function loadUserStats() {
    console.log('📊 Loading user statistics...');
    const savedStats = localStorage.getItem(`userStats_${currentUser.email}`);
    if (savedStats) {
        userStats = JSON.parse(savedStats);
    }
    updateDashboard();
}

function initializeUserStats() {
    console.log('🆕 Initializing new user stats...');
    userStats = {
        totalQuizzes: 0,
        totalScore: 0,
        pdfsProcessed: 0,
        studyStreak: 1,
        lastActiveDate: new Date().toDateString()
    };
    saveUserStats();
    updateDashboard();
}

function saveUserStats() {
    localStorage.setItem(`userStats_${currentUser.email}`, JSON.stringify(userStats));
}

function updateDashboard() {
    console.log('🔄 Updating dashboard display...');
    
    // Update stat numbers
    document.getElementById('totalQuizzes').textContent = userStats.totalQuizzes;
    document.getElementById('averageScore').textContent = 
        userStats.totalQuizzes > 0 ? Math.round(userStats.totalScore / userStats.totalQuizzes) + '%' : '0%';
    document.getElementById('totalPDFs').textContent = userStats.pdfsProcessed;
    document.getElementById('studyStreak').textContent = userStats.studyStreak;
    
    updateRecentActivity();
}

function updateRecentActivity() {
    const activityContainer = document.getElementById('recentActivity');
    const recentQuizzes = JSON.parse(localStorage.getItem(`recentQuizzes_${currentUser.email}`) || '[]');
    
    if (recentQuizzes.length === 0) {
        activityContainer.innerHTML = '<p style="color: #666; text-align: center; padding: 40px;">No activity yet. Upload your first PDF to get started!</p>';
        return;
    }
    
    let activityHTML = '';
    recentQuizzes.slice(0, 5).forEach(quiz => {
        const date = new Date(quiz.date).toLocaleDateString();
        const scoreColor = quiz.score >= 80 ? '#28a745' : quiz.score >= 60 ? '#ffc107' : '#dc3545';
        
        activityHTML += `
            <div style="padding: 15px; border-left: 4px solid ${scoreColor}; margin-bottom: 15px; background: #f8f9fa; border-radius: 0 8px 8px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${quiz.title}</strong>
                        <p style="color: #666; margin: 5px 0;">Score: ${quiz.score}% • ${quiz.questionsTotal} questions</p>
                        <small style="color: #999;">${date}</small>
                    </div>
                    <div style="font-size: 2em;">${quiz.score >= 80 ? '🏆' : quiz.score >= 60 ? '👍' : '📚'}</div>
                </div>
            </div>
        `;
    });
    
    activityContainer.innerHTML = activityHTML;
}

// Notification Function
function showNotification(message, type = 'success') {
    console.log(`🔔 Notification: ${message}`);
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = 'notification ' + (type === 'error' ? 'error' : type === 'info' ? 'info' : '');
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}
// CRUD Operations Functions
function setupCRUDEventListeners() {
    console.log('🛠️ Setting up CRUD event listeners...');
    
    // CRUD tab navigation
    const crudTabs = document.querySelectorAll('.crud-tab');
    crudTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const crudType = this.getAttribute('data-crud');
            showCRUDSection(crudType, this);
        });
    });
}

function showCRUDSection(crudType, clickedTab) {
    console.log(`🔧 Switching to CRUD section: ${crudType}`);
    
    // Hide all CRUD sections
    const crudSections = document.querySelectorAll('.crud-section');
    crudSections.forEach(section => section.classList.remove('active'));
    
    // Remove active class from all CRUD tabs
    const crudTabs = document.querySelectorAll('.crud-tab');
    crudTabs.forEach(tab => tab.classList.remove('active'));
    
    // Show selected CRUD section
    const targetSection = document.getElementById(`crud-${crudType}`);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Add active class to clicked tab
    if (clickedTab) {
        clickedTab.classList.add('active');
    }
}

// USER CRUD Operations
function createUser() {
    console.log('👥 Creating new user...');
    
    const name = document.getElementById('createUserName').value;
    const email = document.getElementById('createUserEmail').value;
    const role = document.getElementById('createUserRole').value;
    
    if (!name || !email || !role) {
        showNotification('Please fill in all fields for user creation.', 'error');
        return;
    }
    
    const newUser = {
        id: Date.now(),
        name: name,
        email: email,
        role: role,
        createdAt: new Date().toISOString()
    };
    
    // Save to localStorage (simulating database)
    const users = JSON.parse(localStorage.getItem('appUsers') || '[]');
    users.push(newUser);
    localStorage.setItem('appUsers', JSON.stringify(users));
    
    // Display result
    displayCRUDResult('user', `✅ User created successfully!<br><strong>ID:</strong> ${newUser.id}<br><strong>Name:</strong> ${newUser.name}<br><strong>Email:</strong> ${newUser.email}<br><strong>Role:</strong> ${newUser.role}`);
    
    // Clear form
    document.getElementById('createUserName').value = '';
    document.getElementById('createUserEmail').value = '';
    document.getElementById('createUserRole').value = '';
    
    showNotification('User created successfully!', 'success');
}

function searchUsers() {
    console.log('🔍 Searching users...');
    
    const searchTerm = document.getElementById('searchUser').value.toLowerCase();
    const users = JSON.parse(localStorage.getItem('appUsers') || '[]');
    
    if (searchTerm) {
        const filteredUsers = users.filter(user => 
            user.name.toLowerCase().includes(searchTerm) || 
            user.email.toLowerCase().includes(searchTerm)
        );
        displayUserList(filteredUsers, `Search results for "${searchTerm}"`);
    } else {
        showNotification('Please enter a search term.', 'error');
    }
}

function getAllUsers() {
    console.log('📖 Getting all users...');
    
    const users = JSON.parse(localStorage.getItem('appUsers') || '[]');
    displayUserList(users, 'All Users');
}

function displayUserList(users, title) {
    let resultHTML = `<strong>${title}:</strong><br><br>`;
    
    if (users.length === 0) {
        resultHTML += 'No users found.';
    } else {
        users.forEach(user => {
            resultHTML += `
                <div style="border: 1px solid #4a5568; margin: 10px 0; padding: 10px; border-radius: 5px;">
                    <strong>ID:</strong> ${user.id}<br>
                    <strong>Name:</strong> ${user.name}<br>
                    <strong>Email:</strong> ${user.email}<br>
                    <strong>Role:</strong> ${user.role}<br>
                    <strong>Created:</strong> ${new Date(user.createdAt).toLocaleString()}
                </div>
            `;
        });
    }
    
    displayCRUDResult('user', resultHTML);
}

function updateUser() {
    console.log('✏️ Updating user...');
    
    const userId = document.getElementById('updateUserId').value;
    const newName = document.getElementById('updateUserName').value;
    const newEmail = document.getElementById('updateUserEmail').value;
    const newRole = document.getElementById('updateUserRole').value;
    
    if (!userId) {
        showNotification('Please enter a User ID to update.', 'error');
        return;
    }
    
    const users = JSON.parse(localStorage.getItem('appUsers') || '[]');
    const userIndex = users.findIndex(user => user.id == userId);
    
    if (userIndex === -1) {
        displayCRUDResult('user', `❌ User with ID ${userId} not found.`);
        return;
    }
    
    // Update user data
    if (newName) users[userIndex].name = newName;
    if (newEmail) users[userIndex].email = newEmail;
    if (newRole) users[userIndex].role = newRole;
    users[userIndex].updatedAt = new Date().toISOString();
    
    localStorage.setItem('appUsers', JSON.stringify(users));
    
    displayCRUDResult('user', `✅ User updated successfully!<br><strong>ID:</strong> ${users[userIndex].id}<br><strong>New Data:</strong><br>Name: ${users[userIndex].name}<br>Email: ${users[userIndex].email}<br>Role: ${users[userIndex].role}`);
    
    // Clear form
    document.getElementById('updateUserId').value = '';
    document.getElementById('updateUserName').value = '';
    document.getElementById('updateUserEmail').value = '';
    document.getElementById('updateUserRole').value = '';
    
    showNotification('User updated successfully!', 'success');
}

function deleteUser() {
    console.log('🗑️ Deleting user...');
    
    const userId = document.getElementById('deleteUserId').value;
    
    if (!userId) {
        showNotification('Please enter a User ID to delete.', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone!')) {
        return;
    }
    
    const users = JSON.parse(localStorage.getItem('appUsers') || '[]');
    const userIndex = users.findIndex(user => user.id == userId);
    
    if (userIndex === -1) {
        displayCRUDResult('user', `❌ User with ID ${userId} not found.`);
        return;
    }
    
    const deletedUser = users.splice(userIndex, 1)[0];
    localStorage.setItem('appUsers', JSON.stringify(users));
    
    displayCRUDResult('user', `✅ User deleted successfully!<br><strong>Deleted User:</strong><br>ID: ${deletedUser.id}<br>Name: ${deletedUser.name}<br>Email: ${deletedUser.email}`);
    
    document.getElementById('deleteUserId').value = '';
    showNotification('User deleted successfully!', 'success');
}

function displayCRUDResult(type, content) {
    const resultDiv = document.getElementById(`${type}ResultsContent`);
    if (resultDiv) {
        resultDiv.innerHTML = content;
    }
}
// QUIZ CRUD Operations
function createQuiz() {
    console.log('📝 Creating new quiz...');
    
    const title = document.getElementById('createQuizTitle').value;
    const difficulty = document.getElementById('createQuizDifficulty').value;
    const questions = document.getElementById('createQuizQuestions').value;
    
    if (!title || !difficulty || !questions) {
        showNotification('Please fill in all fields for quiz creation.', 'error');
        return;
    }
    
    const newQuiz = {
        id: Date.now(),
        title: title,
        difficulty: difficulty,
        questionCount: parseInt(questions),
        createdBy: currentUser ? currentUser.email : 'System',
        createdAt: new Date().toISOString()
    };
    
    const quizzes = JSON.parse(localStorage.getItem('appQuizzes') || '[]');
    quizzes.push(newQuiz);
    localStorage.setItem('appQuizzes', JSON.stringify(quizzes));
    
    displayCRUDResult('quiz', `✅ Quiz created successfully!<br><strong>ID:</strong> ${newQuiz.id}<br><strong>Title:</strong> ${newQuiz.title}<br><strong>Difficulty:</strong> ${newQuiz.difficulty}<br><strong>Questions:</strong> ${newQuiz.questionCount}`);
    
    // Clear form
    document.getElementById('createQuizTitle').value = '';
    document.getElementById('createQuizDifficulty').selectedIndex = 0;
    document.getElementById('createQuizQuestions').value = '';
    
    showNotification('Quiz created successfully!', 'success');
}

function searchQuizzes() {
    console.log('🔍 Searching quizzes...');
    
    const searchTerm = document.getElementById('searchQuiz').value.toLowerCase();
    const quizzes = JSON.parse(localStorage.getItem('appQuizzes') || '[]');
    
    if (searchTerm) {
        const filteredQuizzes = quizzes.filter(quiz => 
            quiz.title.toLowerCase().includes(searchTerm)
        );
        displayQuizList(filteredQuizzes, `Search results for "${searchTerm}"`);
    } else {
        showNotification('Please enter a search term.', 'error');
    }
}

function getAllQuizzes() {
    console.log('📖 Getting all quizzes...');
    
    const quizzes = JSON.parse(localStorage.getItem('appQuizzes') || '[]');
    displayQuizList(quizzes, 'All Quizzes');
}

function displayQuizList(quizzes, title) {
    let resultHTML = `<strong>${title}:</strong><br><br>`;
    
    if (quizzes.length === 0) {
        resultHTML += 'No quizzes found.';
    } else {
        quizzes.forEach(quiz => {
            resultHTML += `
                <div style="border: 1px solid #4a5568; margin: 10px 0; padding: 10px; border-radius: 5px;">
                    <strong>ID:</strong> ${quiz.id}<br>
                    <strong>Title:</strong> ${quiz.title}<br>
                    <strong>Difficulty:</strong> ${quiz.difficulty}<br>
                    <strong>Questions:</strong> ${quiz.questionCount}<br>
                    <strong>Created By:</strong> ${quiz.createdBy}<br>
                    <strong>Created:</strong> ${new Date(quiz.createdAt).toLocaleString()}
                </div>
            `;
        });
    }
    
    displayCRUDResult('quiz', resultHTML);
}

function updateQuiz() {
    console.log('✏️ Updating quiz...');
    
    const quizId = document.getElementById('updateQuizId').value;
    const newTitle = document.getElementById('updateQuizTitle').value;
    const newDifficulty = document.getElementById('updateQuizDifficulty').value;
    
    if (!quizId) {
        showNotification('Please enter a Quiz ID to update.', 'error');
        return;
    }
    
    const quizzes = JSON.parse(localStorage.getItem('appQuizzes') || '[]');
    const quizIndex = quizzes.findIndex(quiz => quiz.id == quizId);
    
    if (quizIndex === -1) {
        displayCRUDResult('quiz', `❌ Quiz with ID ${quizId} not found.`);
        return;
    }
    
    if (newTitle) quizzes[quizIndex].title = newTitle;
    if (newDifficulty) quizzes[quizIndex].difficulty = newDifficulty;
    quizzes[quizIndex].updatedAt = new Date().toISOString();
    
    localStorage.setItem('appQuizzes', JSON.stringify(quizzes));
    
    displayCRUDResult('quiz', `✅ Quiz updated successfully!<br><strong>ID:</strong> ${quizzes[quizIndex].id}<br><strong>Title:</strong> ${quizzes[quizIndex].title}<br><strong>Difficulty:</strong> ${quizzes[quizIndex].difficulty}`);
    
    document.getElementById('updateQuizId').value = '';
    document.getElementById('updateQuizTitle').value = '';
    document.getElementById('updateQuizDifficulty').selectedIndex = 0;
    
    showNotification('Quiz updated successfully!', 'success');
}

function deleteQuiz() {
    console.log('🗑️ Deleting quiz...');
    
    const quizId = document.getElementById('deleteQuizId').value;
    
    if (!quizId) {
        showNotification('Please enter a Quiz ID to delete.', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this quiz? This action cannot be undone!')) {
        return;
    }
    
    const quizzes = JSON.parse(localStorage.getItem('appQuizzes') || '[]');
    const quizIndex = quizzes.findIndex(quiz => quiz.id == quizId);
    
    if (quizIndex === -1) {
        displayCRUDResult('quiz', `❌ Quiz with ID ${quizId} not found.`);
        return;
    }
    
    const deletedQuiz = quizzes.splice(quizIndex, 1)[0];
    localStorage.setItem('appQuizzes', JSON.stringify(quizzes));
    
    displayCRUDResult('quiz', `✅ Quiz deleted successfully!<br><strong>Deleted Quiz:</strong><br>ID: ${deletedQuiz.id}<br>Title: ${deletedQuiz.title}<br>Difficulty: ${deletedQuiz.difficulty}`);
    
    document.getElementById('deleteQuizId').value = '';
    showNotification('Quiz deleted successfully!', 'success');
}

// PDF and Feedback CRUD (simplified versions)
function getAllPDFs() {
    console.log('📄 Getting all PDFs...');
    const pdfs = JSON.parse(localStorage.getItem('appPDFs') || '[]');
    
    let resultHTML = '<strong>All PDFs:</strong><br><br>';
    if (pdfs.length === 0) {
        resultHTML += 'No PDFs uploaded yet.';
    } else {
        pdfs.forEach(pdf => {
            resultHTML += `
                <div style="border: 1px solid #4a5568; margin: 10px 0; padding: 10px; border-radius: 5px;">
                    <strong>ID:</strong> ${pdf.id}<br>
                    <strong>Name:</strong> ${pdf.name}<br>
                    <strong>Size:</strong> ${pdf.size}<br>
                    <strong>Uploaded:</strong> ${new Date(pdf.uploadDate).toLocaleString()}
                </div>
            `;
        });
    }
    
    displayCRUDResult('pdf', resultHTML);
}

function getAllFeedback() {
    console.log('💬 Getting all feedback...');
    const feedback = JSON.parse(localStorage.getItem('appFeedback') || '[]');
    
    let resultHTML = '<strong>All Feedback:</strong><br><br>';
    if (feedback.length === 0) {
        resultHTML += 'No feedback submitted yet.';
    } else {
        feedback.forEach(fb => {
            resultHTML += `
                <div style="border: 1px solid #4a5568; margin: 10px 0; padding: 10px; border-radius: 5px;">
                    <strong>ID:</strong> ${fb.id}<br>
                    <strong>Rating:</strong> ${'★'.repeat(fb.rating)}${'☆'.repeat(5-fb.rating)}<br>
                    <strong>Comment:</strong> ${fb.text || 'No comment'}<br>
                    <strong>Date:</strong> ${new Date(fb.date).toLocaleString()}
                </div>
            `;
        });
    }
    
    displayCRUDResult('feedback', resultHTML);
}

// Make App Downloadable
function downloadApp() {
    console.log('💾 Preparing app for download...');
    
    showNotification('Preparing your app for download...', 'info');
    
    // Get all the code
    const htmlContent = document.documentElement.outerHTML;
    const cssContent = getCSSContent();
    const jsContent = getJSContent();
    
    // Create a complete HTML file with embedded CSS and JS
    const completeApp = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScholarQuiz - AI Quiz Generator</title>
    <style>
${cssContent}
    </style>
</head>
<body>
${document.body.innerHTML}
    <script>
${jsContent}
    </script>
</body>
</html>`;

    // Create download
    const blob = new Blob([completeApp], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ScholarQuiz-App.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showNotification('App downloaded successfully! 🎉', 'success');
}

function getCSSContent() {
    // This would normally get CSS from your file, but for simplicity:
    return '/* Your beautiful CSS styles would be embedded here */';
}

function getJSContent() {
    // This would normally get JS from your file, but for simplicity:
    return '/* Your interactive JavaScript would be embedded here */';
}

// Initialize CRUD when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupCRUDEventListeners();
    
    // Add download button to dashboard
    setTimeout(() => {
        const dashboard = document.getElementById('dashboard');
        if (dashboard) {
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'btn btn-primary';
            downloadBtn.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1000; padding: 15px 20px;';
            downloadBtn.innerHTML = '💾 Download App';
            downloadBtn.addEventListener('click', downloadApp);
            document.body.appendChild(downloadBtn);
        }
    }, 2000);
});
// PDF Upload Fix
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for everything to load
    setTimeout(() => {
        setupPDFUpload();
    }, 1000);
});

function setupPDFUpload() {
    console.log('🔧 Setting up PDF upload...');
    
    const pdfUploadArea = document.getElementById('pdfUploadArea');
    const pdfFileInput = document.getElementById('pdfFile');
    const browseBtn = document.getElementById('browseBtn');

    if (pdfUploadArea && pdfFileInput && browseBtn) {
        // Click to browse
        pdfUploadArea.addEventListener('click', () => {
            pdfFileInput.click();
        });
        
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            pdfFileInput.click();
        });

        // File selection
        pdfFileInput.addEventListener('change', handleFileSelect);

        // Drag and drop
        pdfUploadArea.addEventListener('drop', handleDrop);
        pdfUploadArea.addEventListener('dragover', handleDragOver);
        pdfUploadArea.addEventListener('dragenter', handleDragEnter);
        pdfUploadArea.addEventListener('dragleave', handleDragLeave);
        
        console.log('✅ PDF upload setup complete!');
    } else {
        console.log('❌ PDF upload elements not found');
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
        simulatePDFProcessing(file);
    } else {
        showNotification('Please select a valid PDF file.', 'error');
    }
}

function handleDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        simulatePDFProcessing(files[0]);
    } else {
        showNotification('Please upload a valid PDF file.', 'error');
    }
}

function handleDragOver(event) {
    event.preventDefault();
}

function handleDragEnter(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
}

function simulatePDFProcessing(file) {
    console.log('📄 Processing PDF:', file.name);
    
    showNotification('Processing PDF...', 'info');
    
    // Show progress
    const progressDiv = document.getElementById('uploadProgress');
    const previewDiv = document.getElementById('pdfPreview');
    
    if (progressDiv) {
        progressDiv.style.display = 'block';
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += 20;
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            
            if (progressBar) progressBar.style.width = progress + '%';
            if (progressText) {
                if (progress === 20) progressText.textContent = 'Reading PDF...';
                else if (progress === 40) progressText.textContent = 'Extracting text...';
                else if (progress === 60) progressText.textContent = 'Processing content...';
                else if (progress === 80) progressText.textContent = 'Generating preview...';
                else if (progress === 100) progressText.textContent = 'Complete!';
            }
            
            if (progress >= 100) {
                clearInterval(interval);
                
                // Hide progress and show preview
                setTimeout(() => {
                    if (progressDiv) progressDiv.style.display = 'none';
                    showPDFPreview(file);
                    showNotification('PDF processed successfully!', 'success');
                }, 500);
            }
        }, 800);
    }
}

function showPDFPreview(file) {
    console.log('👀 Showing PDF preview...');
    
    const previewDiv = document.getElementById('pdfPreview');
    if (previewDiv) {
        // Fill in the preview information
        const fileName = document.getElementById('fileName');
        const pageCount = document.getElementById('pageCount');
        const fileSize = document.getElementById('fileSize');
        const textPreview = document.getElementById('textPreview');
        
        if (fileName) fileName.textContent = file.name;
        if (pageCount) pageCount.textContent = Math.floor(Math.random() * 50) + 1; // Random pages
        if (fileSize) fileSize.textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
        if (textPreview) textPreview.textContent = 'This is a sample preview of the PDF content. In a real app, this would show the actual extracted text from your PDF document...';
        
        previewDiv.style.display = 'block';
        
        // Setup generate quiz button
        const generateBtn = document.getElementById('generateQuizBtn');
        if (generateBtn) {
            generateBtn.addEventListener('click', function() {
                showNotification('Quiz generation feature coming soon!', 'info');
                showSection('quiz');
            });
        }
    }
}
// Quick PDF Fix
setTimeout(() => {
    const btn = document.getElementById('browseBtn');
    const input = document.getElementById('pdfFile');
    if (btn && input) {
        btn.onclick = () => input.click();
    }
}, 2000);