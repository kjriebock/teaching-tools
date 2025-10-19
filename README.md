<<<<<<< HEAD
# Teaching Tools

A collection of interactive web applications for science education.

## Tools Included

### 1. Statistical Test Selector

An interactive web application that helps students select the appropriate statistical test for their research data using a decision tree approach.

**Features:**
- Interactive Decision Tree with breadcrumb navigation
- Help modals with detailed explanations
- Links to online statistical calculators
- Back and Start Over navigation buttons
- Responsive design for all devices

**Statistical Tests Covered:**
- Chi-Squared Test for Independence
- One-Way ANOVA for Independent Measures
- t-test for Independent Samples
- Mann-Whitney U Test
- R-squared Coefficient of Determination (R²)
- Pearson Correlation Coefficient (r)
- Spearman's Rank Correlation Coefficient (ρ)

**Files:**
- `index.html` - Statistical test selector interface
- `data/decision-tree.json` - Decision tree logic
- `js/app.js` - Application JavaScript
- `styles/main.css` - Styling
- `objectives.md` - Original requirements

### 2. Predator-Prey Ecosystem Simulation

An interactive three-species predator-prey model demonstrating population dynamics in different environmental conditions.

**Features:**
- Three-Species Model: Producer (🌱), Prey (🐰), and Predator (🦉) populations
- Environmental Conditions: Toggle between "Average Rainfall" and "Drought"
- Real-time Visualization: Live population bars and time-series charts
- Lotka-Volterra Dynamics: Mathematical modeling of species interactions

**Files:**
- `predator-prey-model.html` - Main simulation
- `predator-prey-model-backup.html` - Backup version
- `stable-equilibrium-simulation.html` - Stable equilibrium model

## Running the Applications

### Option 1: Direct File Opening
Simply double-click any `.html` file to open it in your default browser.

### Option 2: Local Server (Recommended)
For the best experience, run a local server:

```bash
# Using Python 3
python3 -m http.server 8000

# Then navigate to:
# http://localhost:8000/index.html (Statistical Test Selector)
# http://localhost:8000/predator-prey-model.html (Ecosystem Simulation)
```

## Browser Compatibility

Works with all modern browsers:
- Chrome
- Firefox
- Safari
- Edge

## License

Free to use for educational purposes.
=======
# Predator-Prey Ecosystem Simulation

An interactive three-species predator-prey model demonstrating population dynamics in different environmental conditions.

## Features

- **Three-Species Model**: Producer (🌱), Prey (🐰), and Predator (🦉) populations
- **Environmental Conditions**: Toggle between "Average Rainfall" and "Drought" conditions
- **Real-time Visualization**: Live population bars and time-series charts
- **Lotka-Volterra Dynamics**: Mathematical modeling of species interactions

## How to Use

1. Open `predator-prey-model.html` in a web browser
2. Select environmental conditions (Average Rainfall or Drought)
3. Click "Start" to begin the simulation
4. Watch population dynamics unfold over 100 months
5. Use "Reset" to restart with different conditions

## Environmental Effects

- **Average Rainfall**: Normal ecosystem carrying capacity
- **Drought**: All population sizes reduced by 50% to simulate resource scarcity

## Files

- `predator-prey-model.html` - Main simulation file
- `predator-prey-model-backup.html` - Backup version
- `README.md` - This documentation

## Technology

- Pure HTML/CSS/JavaScript
- Chart.js for data visualization
- Responsive design for various screen sizes
>>>>>>> 887fe99a656248afe38c321bb36821d3af6a2ca2
