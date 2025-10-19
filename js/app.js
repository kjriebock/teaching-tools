// Statistical Test Selector App
class StatisticalTestSelector {
    constructor() {
        this.decisionTree = null;
        this.currentNode = null;
        this.history = [];
        this.currentRecommendation = null;
        this.init();
    }

    async init() {
        try {
            await this.loadDecisionTree();
            this.setupEventListeners();
            this.startDecisionTree();
        } catch (error) {
            console.error('Error initializing app:', error);
            this.showError('Failed to load the decision tree. Please refresh the page.');
        }
    }

    async loadDecisionTree() {
        const response = await fetch('data/decision-tree.json');
        if (!response.ok) {
            throw new Error('Failed to load decision tree data');
        }
        this.decisionTree = await response.json();
    }

    setupEventListeners() {
        document.getElementById('back-btn').addEventListener('click', () => this.goBack());
        document.getElementById('start-over-btn').addEventListener('click', () => this.restart());
        document.getElementById('restart-btn').addEventListener('click', () => this.restart());
        document.getElementById('help-btn').addEventListener('click', () => this.showHelp());
        
        // Modal close handlers
        document.getElementById('modal-close-btn').addEventListener('click', () => this.closeModal());
        document.getElementById('modal-ok-btn').addEventListener('click', () => this.closeModal());
        
        // Close modal when clicking outside
        document.getElementById('help-modal').addEventListener('click', (e) => {
            if (e.target.id === 'help-modal') {
                this.closeModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    startDecisionTree() {
        this.history = [];
        this.currentNode = this.decisionTree.startNode;
        this.currentRecommendation = null;
        this.displayNode();
        this.updateBreadcrumb();
    }

    displayNode() {
        const node = this.decisionTree.nodes[this.currentNode];
        
        if (!node) {
            this.showError('Invalid node in decision tree');
            return;
        }

        // Show question card, hide result card
        document.getElementById('question-card').style.display = 'block';
        document.getElementById('result-card').style.display = 'none';

        // Display context if available
        const contextDiv = document.getElementById('context');
        if (node.context) {
            contextDiv.textContent = node.context;
            contextDiv.style.display = 'block';
        } else {
            contextDiv.style.display = 'none';
        }

        // Display question
        document.getElementById('question-text').textContent = node.question;

        // Show/hide help button based on whether help is available
        const helpBtn = document.getElementById('help-btn');
        if (node.helpNeeded && this.decisionTree.helpTopics[node.helpNeeded]) {
            helpBtn.style.display = 'flex';
            helpBtn.setAttribute('data-help-topic', node.helpNeeded);
        } else {
            helpBtn.style.display = 'none';
        }

        // Display test link if available (normality test or Shapiro-Wilk test)
        const testLinkDiv = document.getElementById('test-link');
        if (node.normalityTestUrl) {
            testLinkDiv.innerHTML = `
                <div class="test-link-section">
                    <p><strong>Not sure if your data is normally distributed?</strong></p>
                    <a href="${node.normalityTestUrl}" target="_blank" rel="noopener noreferrer" class="test-link-btn">
                        <span class="test-icon">📊</span>
                        Test for Normal Distribution
                        <span class="external-icon">↗</span>
                    </a>
                </div>
            `;
            testLinkDiv.style.display = 'block';
        } else if (node.shapiroWilkUrl) {
            testLinkDiv.innerHTML = `
                <div class="test-link-section shapiro-wilk">
                    <p><strong>Use this calculator to run the Shapiro-Wilk test:</strong></p>
                    <a href="${node.shapiroWilkUrl}" target="_blank" rel="noopener noreferrer" class="test-link-btn">
                        <span class="test-icon">📈</span>
                        Run Shapiro-Wilk Test on Residuals
                        <span class="external-icon">↗</span>
                    </a>
                </div>
            `;
            testLinkDiv.style.display = 'block';
        } else {
            testLinkDiv.style.display = 'none';
        }

        // Display answers
        const answersDiv = document.getElementById('answers');
        answersDiv.innerHTML = '';

        node.answers.forEach((answer, index) => {
            const button = document.createElement('button');
            button.className = 'answer-btn';
            button.textContent = answer.answer;
            button.addEventListener('click', () => this.handleAnswer(answer));
            answersDiv.appendChild(button);
        });

        // Update back button visibility
        const backBtn = document.getElementById('back-btn');
        backBtn.style.display = this.history.length > 0 ? 'block' : 'none';
        
        // Update start over button visibility
        const startOverBtn = document.getElementById('start-over-btn');
        startOverBtn.style.display = this.history.length > 0 ? 'block' : 'none';
    }

    handleAnswer(answer) {
        // Save current state to history
        this.history.push({
            node: this.currentNode,
            answer: answer.answer
        });

        if (answer.recommendation) {
            // Show result
            this.currentRecommendation = answer;
            this.displayResult(answer);
        } else if (answer.nextNode) {
            // Move to next node
            this.currentNode = answer.nextNode;
            this.displayNode();
            this.updateBreadcrumb();
        }
    }

    displayResult(answer) {
        // Hide question card, show result card
        document.getElementById('question-card').style.display = 'none';
        document.getElementById('result-card').style.display = 'block';

        // Display test name
        document.getElementById('test-name').textContent = answer.recommendation;

        // Display conditions if available, with help button
        const conditionsDiv = document.getElementById('conditions');
        if (answer.conditions) {
            // Split conditions by bullet points
            const conditionLines = answer.conditions.split('\n');
            let conditionsHTML = '';
            
            // Track which help topics we need
            const helpTopics = [];
            if (answer.helpNeeded) helpTopics.push(answer.helpNeeded);
            if (answer.additionalHelpTopics) helpTopics.push(...answer.additionalHelpTopics);
            
            conditionLines.forEach((line, index) => {
                if (line.trim()) {
                    conditionsHTML += `<div class="condition-line"><span>${line}</span>`;
                    
                    // Add help icon for first bullet (measurement types or chi-squared expected)
                    if (index === 0 && (helpTopics.includes('measurementTypes') || helpTopics.includes('chiSquaredExpected'))) {
                        const topic = helpTopics.includes('measurementTypes') ? 'measurementTypes' : 'chiSquaredExpected';
                        conditionsHTML += `<button class="help-btn-inline" data-help-topic="${topic}" title="Click for explanation">
                                <span class="help-icon">?</span>
                            </button>`;
                    }
                    
                    // Add help icon for second bullet (normal distribution)
                    if (index === 1 && helpTopics.includes('normalDistribution')) {
                        conditionsHTML += `<button class="help-btn-inline" data-help-topic="normalDistribution" title="Click for explanation">
                                <span class="help-icon">?</span>
                            </button>`;
                    }
                    
                    conditionsHTML += '</div>';
                }
            });
            
            conditionsDiv.innerHTML = conditionsHTML;
            
            // Add click handlers to all inline help buttons
            conditionsDiv.querySelectorAll('.help-btn-inline').forEach(btn => {
                btn.addEventListener('click', () => {
                    const topic = btn.getAttribute('data-help-topic');
                    this.showHelpForTopic(topic);
                });
            });
            
            conditionsDiv.style.display = 'block';
        } else {
            conditionsDiv.style.display = 'none';
        }

        // Display calculator link if available
        const calculatorDiv = document.getElementById('calculator-link');
        if (answer.calculatorUrl) {
            calculatorDiv.innerHTML = `
                <div class="calculator-section">
                    <h3>Calculate Your Test:</h3>
                    <a href="${answer.calculatorUrl}" target="_blank" rel="noopener noreferrer" class="calculator-btn">
                        <span class="calculator-icon">🔢</span>
                        Open ${answer.calculatorName || 'Calculator'}
                        <span class="external-icon">↗</span>
                    </a>
                </div>
            `;
            calculatorDiv.style.display = 'block';
        } else {
            calculatorDiv.style.display = 'none';
        }

        // Update back button visibility
        document.getElementById('back-btn').style.display = 'block';
        
        // Update start over button visibility
        document.getElementById('start-over-btn').style.display = 'block';
    }

    updateBreadcrumb() {
        const breadcrumb = document.getElementById('breadcrumb');
        
        if (this.history.length === 0) {
            breadcrumb.innerHTML = '<span class="breadcrumb-item">Start</span>';
        } else {
            const items = this.history.map((item, index) => {
                return `<span class="breadcrumb-item">${item.answer}</span>`;
            });
            breadcrumb.innerHTML = '<span class="breadcrumb-item">Start</span>' + items.join('');
        }
    }

    showHelp() {
        const helpBtn = document.getElementById('help-btn');
        const helpTopic = helpBtn.getAttribute('data-help-topic');
        this.showHelpForTopic(helpTopic);
    }

    showHelpForTopic(helpTopic) {
        if (helpTopic && this.decisionTree.helpTopics[helpTopic]) {
            const topic = this.decisionTree.helpTopics[helpTopic];
            document.getElementById('modal-title').textContent = topic.title;
            document.getElementById('modal-content').textContent = topic.content;
            document.getElementById('help-modal').style.display = 'flex';
        }
    }

    closeModal() {
        document.getElementById('help-modal').style.display = 'none';
    }

    goBack() {
        if (this.history.length === 0) return;

        // Check if we're currently showing a result
        const resultCard = document.getElementById('result-card');
        if (resultCard.style.display === 'block') {
            // Go back from result to the last question
            const lastState = this.history[this.history.length - 1];
            this.currentNode = lastState.node;
            this.currentRecommendation = null;
            this.history.pop();
            this.displayNode();
            this.updateBreadcrumb();
        } else {
            // Go back from current question to previous question
            // The last item in history is the node we just came from
            // Pop it to remove current state
            this.history.pop();
            
            if (this.history.length === 0) {
                // No more history, go back to start
                this.currentNode = this.decisionTree.startNode;
            } else {
                // Go back to the previous node
                const previousState = this.history[this.history.length - 1];
                this.currentNode = previousState.node;
            }
            
            this.displayNode();
            this.updateBreadcrumb();
        }
    }

    restart() {
        this.startDecisionTree();
    }

    showError(message) {
        const questionCard = document.getElementById('question-card');
        questionCard.innerHTML = `
            <div style="text-align: center; color: #dc3545;">
                <h2>⚠️ Error</h2>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new StatisticalTestSelector();
});
