import sys
import pandas as pd
from scipy.stats import shapiro
data_sheet_2 = pd.read_excel('/mnt/c/Users/olutu/Downloads/record_of_interactions.xlsx', sheet_name='Sheet2')
print(data_sheet_2[['Participants ID','Story Recall']].head())

likert_map = {
    "Very happy": 4,
    "Happy": 3,
    "Okay": 2,
    "Sad": 1,
    "Very sad": 0
}



data_sheet_2["baseline_robot_sentiment_coded"] = data_sheet_2["baseline_robot_sentiment"].map(likert_map)
data_sheet_2["postsession_robot_sentiment_coded"] = data_sheet_2["postsession_robot_sentiment"].map(likert_map)
data_sheet_2['story_related_emotion_coded'] = data_sheet_2['story_related_emotion'].map(likert_map)

ai_group = data_sheet_2[data_sheet_2['Condition'] == 'AI']['Story Recall'].dropna().astype(int)
control_group = data_sheet_2[data_sheet_2['Condition'] == 'Control']['Story Recall'].dropna().astype(int)

print(ai_group.head())
print("---------")
print(control_group.head())
# Step 2: Shapiro-Wilk test
shapiro_ai = shapiro(ai_group)
shapiro_control = shapiro(control_group)

print("AI group: W = {:.3f}, p = {:.3f}".format(shapiro_ai.statistic, shapiro_ai.pvalue))
print("Control group: W = {:.3f}, p = {:.3f}".format(shapiro_control.statistic, shapiro_control.pvalue))