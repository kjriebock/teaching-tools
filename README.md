# Statistical Test Selector

An interactive web application that helps students select the appropriate statistical test for their research data using a decision tree approach.

## Features

- **Interactive Decision Tree**: Guides users through questions to determine the best statistical test
- **Breadcrumb Navigation**: Shows the path taken through the decision tree
- **Back Button**: Allows users to revisit previous questions
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Clean, student-friendly interface with smooth animations

## Statistical Tests Covered

- Chi-Squared Test
- ANOVA (Analysis of Variance)
- t-test
- Mann-Whitney U Test
- R-squared Coefficient of Determination (R²)
- Pearson Correlation Coefficient (r)
- Spearman's Rank Correlation Coefficient (ρ)

## Project Structure

```
statistical-test-selector/
├── index.html              # Main HTML file
├── data/
│   └── decision-tree.json  # Decision tree logic and questions
├── js/
│   └── app.js             # Application JavaScript
├── styles/
│   └── main.css           # Styling
└── README.md              # This file
```

## How to Use

1. Open `index.html` in a web browser
2. Answer each question based on your research data and experiment design
3. Follow the decision tree until you reach a recommended statistical test
4. Review the conditions and assumptions for the recommended test
5. Use the "Back" button to explore different paths or "Start Over" to begin again

## Running the Application

### Option 1: Direct File Opening
Simply double-click `index.html` to open it in your default browser.

### Option 2: Local Server (Recommended)
For the best experience, run a local server:

```bash
# Using Python 3
python3 -m http.server 8000

# Using Python 2
python -m SimpleHTTPServer 8000

# Using Node.js (with npx and http-server)
npx http-server -p 8000
```

Then navigate to `http://localhost:8000` in your browser.

## Customization

To modify the decision tree logic or add new tests:

1. Edit `data/decision-tree.json`
2. Follow the existing structure:
   - Each node has a `question` and `answers` array
   - Each answer either leads to a `nextNode` or provides a `recommendation`
   - Optional `conditions` explain requirements for each test
   - Optional `context` provides additional guidance for a question

## Browser Compatibility

Works with all modern browsers:
- Chrome
- Firefox
- Safari
- Edge

## License

Free to use for educational purposes.
