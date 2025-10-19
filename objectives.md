START HERE: Purpose of the Data Analysis
Is the raw data from a single sample being classified according to two different variables (e.g., by both 'gender' and 'voting preference') to determine if there is a significant association or relationship between those two variables?
YES → Use a Chi-Squared Test of Independence
Necessary Condition: The expected values within each group must be at least 5
NO → Proceed to Question 2.

Question 2: Experiment Goal (Differences vs. Correlation)
Is your experiment designed to measure differences between groups (i.e. in a bar chart) or correlation between variables (i.e. in a scatter plot)?
DIFFERENCES → Proceed to Differences Pathway (Question 3)
CORRELATION → Proceed to Correlation Pathway (Question 4)

Differences Pathway (Comparing Groups)
If you are in this pathway, often you have used a bar chart or box & whisker plot to show the differences between groups of your IV and the average DV measurements
How many groups are you comparing (i.e. values of your Independent Variable)?
Three or More Groups → Use One-Way ANOVA (Analysis of Variance) for Independent Measures
Necessary Condition: The DV measurement type must be interval or ratio, and there must be a normal distribution within each group of data.
Exactly Two Groups → Proceed to Question 3a.
Which type of measurement best represents your raw dependent variable data? 
Ordinal → Mann-Whitney U Test
Interval or Ratio → Proceed to Question 3b
Looking at the set of DV data collected for each group, do you see a normal distribution? Meaning that for each group there are some small values, some large values, but most values are centered around the middle.
YES, a normal distribution is evident → t-test for two independent means
Condition is that at least 15 pieces of data are included within each group
NO, a normal distribution is not able to be determined or the data appears to be skewed to one end → Mann-Whitney U Test

Correlation Pathway (Relationships)
If you are in this pathway, typically you have used a scatter plot to show the relationship between your IV and DV
Are you aiming to show how much of the variation in the data can be explained by your chosen line of best fit model?
YES → R-squared Coefficient of Determination (R2)
NO, the aim is to show the strength of the relationship shown by the line of best fit → Proceed to Question 4a
Is the correlation you are aiming to show linear or non-linear?
Linear → Proceed to Question 4b
Non-Linear → Spearman's Rank Correlation Coefficient (ρ) 
It must be determined if the residuals of the mean Y-values of your results show a normal distribution or not. The Shaprio-Wilk test on residuals is a reliable measure for this. On the calculator below, keep the default settings and select the option “Enter Raw Data from Excel”. In a two-column format, paste in your X and Y values along with their headers, with Y-values in the right-hand column. Click the “Calculate” button. Scroll down on the page to the “Validation” section and look for the “Residual normality” result. 
The result of the Shaprio-Wilk test is that the residuals of the mean Y-values are normally distributed → Pearson Correlation Coefficient (r) 
Condition for a highly accurate result: a total sample size of at least 25 values should be present
The result of the Shaprio-Wilk test is that the residuals of the mean Y-values are NOT normally distributed → Spearman's Rank Correlation Coefficient (ρ) 
Necessary Condition: at least 6 values of the IV are required
