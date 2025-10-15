import gradio as gd
import pandas as pd
import matplotlib.pyplot as plt
import datetime

#######################################################################################

def cal_bmi(height, weight, unit_height, unit_weight):
    if unit_height == "inches":
        height_cm = height * 2.54
    else:
        height_cm = height

    if unit_weight == "lbs":
        weight_kg = weight * 0.453592
    else:
        weight_kg = weight

    if height_cm > 0:
        bmi = weight_kg / ((height_cm / 100) ** 2)
        return round(bmi, 2)
    else:
        return 0

#######################################################################################

def get_bmi_category(bmi):
    if bmi == 0:
        return "Please enter valid height and weight."
    elif bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 24.9:
        return "Normal weight"
    elif 25 <= bmi < 29.9:
        return "Overweight"
    else:
        return "Obese"


bmi_history = pd.DataFrame(columns=['Date', 'BMI'])

#######################################################################################


bmi_history = pd.DataFrame(columns=['Date', 'BMI'])
def update_history_and_plot(date, bmi):
    global bmi_history
    if bmi > 0 and date:
        # Convert date string to datetime object for proper plotting
        try:
            date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return gd.Plot() # Return empty plot if date format is incorrect

        new_data = pd.DataFrame([{'Date': date_obj, 'BMI': bmi}])
        bmi_history = pd.concat([bmi_history, new_data], ignore_index=True)
        bmi_history = bmi_history.sort_values(by='Date').reset_index(drop=True) # Sort by date

        plt.figure(figsize=(8, 4))
        plt.plot(bmi_history['Date'], bmi_history['BMI'], marker='o')
        plt.xlabel('Date')
        plt.ylabel('BMI')
        plt.title('BMI Changes Over Time')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        return plt.gcf()
    else:
        return gd.Plot()
#####################################################################################
#####################################################################################
#####################################################################################

def cal_bmr(gender, weight, height, age):
    """Calculates BMR using the Harris-Benedict formula."""
    if gender == "Male":
        # BMR for men
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        # BMR for women
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    return round(bmr, 2)

#####################################################################################

def cal_tdee(bmr, activity_level):
    """Calculates TDEE based on BMR and activity level."""
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Extra Active": 1.9
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.2)
    return round(tdee, 2)

####################################################################################

def cal_calorie_goals(tdee):
    """Returns calorie goals for weight maintenance, loss, and gain."""
    maintenance = tdee
    loss_0_5kg = tdee - 500  # ~0.5 kg/week
    loss_1kg = tdee - 1000   # ~1 kg/week
    gain_0_5kg = tdee + 500
    return maintenance, loss_0_5kg, loss_1kg, gain_0_5kg

######################################################################################
######################################################################################
#####################################################################################

def log_food(manual_calories, food_log_df, tdee):
    import matplotlib.pyplot as plt
    import pandas as pd
    import datetime

    # Ensure the dataframe has proper structure
    if not isinstance(food_log_df, pd.DataFrame) or food_log_df.empty or set(food_log_df.columns) != {'Date', 'Food', 'Calories'}:
        food_log_df = pd.DataFrame(columns=['Date', 'Food', 'Calories'])

    today = datetime.date.today().strftime('%Y-%m-%d')
    calories = 0

    try:
            calories = int(manual_calories)
    except Exception as e:
        # Handle invalid input (e.g. text in manual_calories)
        return 0, plt.figure(), food_log_df, 0

    # If still 0, skip logging
    if calories <= 0:
        return 0, plt.figure(), food_log_df, 0

    # Log the new food entry
    new_entry = pd.DataFrame([{
        'Date': today,
        'Calories': calories
    }])
    food_log_df = pd.concat([food_log_df, new_entry], ignore_index=True)

    # Today's total
    daily_entries_today = food_log_df[food_log_df['Date'] == today]
    current_daily_total = daily_entries_today['Calories'].sum()
    Calorie_difference = current_daily_total - tdee if tdee > 0 else 0

    # Get last 7 days of data
    seven_days_ago = datetime.date.today() - datetime.timedelta(days=6)
    recent_logs = food_log_df[pd.to_datetime(food_log_df['Date']) >= pd.to_datetime(seven_days_ago)]

    plt.figure(figsize=(10, 5))

    if not recent_logs.empty:
        daily_calories_last_7_days = (
            recent_logs.groupby('Date')['Calories']
            .sum()
            .reset_index()
        )
        daily_calories_last_7_days['Date'] = pd.to_datetime(daily_calories_last_7_days['Date'])
        daily_calories_last_7_days = daily_calories_last_7_days.sort_values(by='Date')

        plt.bar(daily_calories_last_7_days['Date'], daily_calories_last_7_days['Calories'], color='skyblue')

    plt.xlabel('Date')
    plt.ylabel('Total Daily Calories')
    plt.title('Daily Calorie Intake (Last 7 Days) vs. TDEE')
    plt.xticks(rotation=45)
    plt.tight_layout()

    if tdee and tdee > 0:
        plt.axhline(y=tdee, color='y', linestyle='--', label=f'TDEE ({tdee})')
        plt.legend()

    return current_daily_total, plt.gcf(), food_log_df, Calorie_difference




with gd.Blocks(theme=gd.themes.Soft(), title="Health & Wellness Dashboard") as demo:
    gd.Markdown("# Your Personal Health & Wellness Dashboard")
    gd.Markdown("This suite of tools helps you track key health metrics and manage your nutrition goals. Use the tabs below to get started.")

    tdee_state = gd.State(value=0) # State variable to store TDEE
    food_log_state = gd.State(value=pd.DataFrame(columns=['Date', 'Food', 'Calories'])) # State variable for food log

    with gd.Tabs():

        with gd.TabItem("BMI Calculator"):
            gd.Markdown("### Body Mass Index (BMI) Calculator")
            gd.Markdown("Calculate your **BMI** to assess your body composition. Enter your height and weight, and optionally a date to track your progress over time.")

            with gd.Row():
                with gd.Column():
                    gd.Markdown("#### Enter Your Measurements")
                    height_input = gd.Number(label="Height", value='')
                    unit_height_dd = gd.Radio(["cm", "inches"], value="cm", label="Unit")
                with gd.Column():
                    weight_input = gd.Number(label="Weight", value='')
                    unit_weight_dd = gd.Radio(["kg", "lbs"], value="kg", label="Unit")

            date_input = gd.Textbox(label="Date (optional, for tracking)", placeholder="YYYY-MM-DD")

            calculate_btn = gd.Button("Calculate BMI")

            gd.Markdown("#### Your BMI Results")
            with gd.Row():
                bmi_output = gd.Number(label="BMI Value", interactive=False)
                category_output = gd.Textbox(label="BMI Category", interactive=False)

            gd.Markdown("### Your BMI Tracking Chart")
            gd.Markdown("Log your BMI over time to visualize your progress on the chart below.")
            bmi_plot_output = gd.Plot()

            calculate_btn.click(
                fn=cal_bmi,
                inputs=[height_input, weight_input, unit_height_dd, unit_weight_dd],
                outputs=bmi_output
            ).then(
                fn=get_bmi_category,
                inputs=bmi_output,
                outputs=category_output
            ).then(
                fn=update_history_and_plot,
                inputs=[date_input, bmi_output],
                outputs=bmi_plot_output
            )

        with gd.TabItem("Daily Metabolic Rate"):
            gd.Markdown("### Daily Metabolic Rate Calculator")
            gd.Markdown("Calculate your **Basal Metabolic Rate (BMR)** and **Total Daily Energy Expenditure (TDEE)**. This helps determine your daily calorie needs.")

            with gd.Column():
                gd.Markdown("#### Enter Your Details")
                with gd.Row():
                    gender_input = gd.Radio(["Male", "Female"], label="Gender", value="Male")
                    age_input = gd.Number(label="Age (years)", value='')
                with gd.Row():
                    height_input_bmr = gd.Number(label="Height (cm)", value='')
                    weight_input_bmr = gd.Number(label="Weight (kg)", value='')

            activity_level_dd = gd.Dropdown(
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"],
                label="Activity Level",
                value="Moderately Active",
                info="Sedentary: little to no exercise; Lightly Active: 1-3 days/week; Moderately Active: 3-5 days/week; Very Active: 6-7 days/week; Extra Active: daily training."
            )

            calculate_bmr_btn = gd.Button("Calculate My TDEE & Goals")

            gd.Markdown("#### Your Metabolic Rates")
            with gd.Row():
                bmr_output = gd.Number(label="Basal Metabolic Rate (BMR) [Calories/day]", interactive=False)
                tdee_output = gd.Number(label="Total Daily Energy Expenditure (TDEE) [Calories/day]", interactive=False)

            gd.Markdown("#### Calorie Goals for Weight Management")
            with gd.Row():
                maintenance_output = gd.Number(label="For Maintenance", interactive=False)
                loss_output = gd.Number(label="For Weight Loss (~0.5 kg/week)", interactive=False)
                gain_output = gd.Number(label="For Weight Gain (~0.5 kg/week)", interactive=False)

            calculate_bmr_btn.click(
                fn=cal_bmr,
                inputs=[gender_input, weight_input_bmr, height_input_bmr, age_input],
                outputs=bmr_output
            ).then(
                fn=cal_tdee,
                inputs=[bmr_output, activity_level_dd],
                outputs=tdee_output
            ).then(
                fn=cal_calorie_goals,
                inputs=tdee_output,
                outputs=[maintenance_output, loss_output, gain_output]
            ).then(
                fn=lambda tdee: tdee,
                inputs=tdee_output,
                outputs=tdee_state
            )

        with gd.Tab("Food Tracker"):
            gd.Markdown("### Daily Calorie & Food Tracker")
            gd.Markdown("Log your daily food intake and see how it compares to your TDEE from the previous tab. Make sure to calculate your TDEE first!")

            gd.Number(tdee_state, label="Your Current TDEE [Calories/day]", interactive=False)

            with gd.Column():
                gd.Markdown("#### Log a Food Item")
                with gd.Row():
                    manual_calories_input = gd.Textbox(label="enter Calories", placeholder="e.g., 250")
                log_food_btn = gd.Button("Log Food")

            gd.Markdown("#### Your Daily Summary")
            with gd.Row():
                daily_total_calories_output = gd.Number(label="Daily Calorie Total", interactive=False)
                calorie_difference_output = gd.Number(label="Calorie Difference (Intake - TDEE)", interactive=False)

            gd.Markdown("### Calorie Intake vs. TDEE")
            gd.Markdown("This chart shows your total daily calorie intake for the last 7 days, with your TDEE shown as a red dashed line.")
            calorie_chart_output = gd.Plot()

            log_food_btn.click(
                fn=log_food,
                inputs=[manual_calories_input, food_log_state, tdee_state],
                outputs=[daily_total_calories_output, calorie_chart_output, food_log_state, calorie_difference_output]
            )

    demo.launch()
