// Replace localStorage with AJAX calls to Flask backend
async function createQuiz(formData) {
    try {
        const response = await fetch('/api/quiz/create', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error creating quiz:', error);
        throw error;
    }
}

async function submitQuizAnswers(quizId, answers) {
    try {
        const response = await fetch(`/api/quiz/${quizId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({answers})
        });
        return await response.json();
    } catch (error) {
        console.error('Error submitting quiz:', error);
        throw error;
    }
}