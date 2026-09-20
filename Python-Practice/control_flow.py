name = input("Enter your name: ")
age = int(input("Enter your age: "))
experience = float(input("Enter your year of experience: "))
skills = input("Enter your skills with comma separted: ")
track = "Intern Track" if experience < 1 else "Junior Track" if experience >=1 and experience <=3 else "Mid-Level Track" if experience >=3 and experience <=6 else "Senior Track"
need_upskilling = "Yes" if not "Python" in skills else "No"

if age >= 18:
    print("===== Application Result =====")
    print(f"Name          : {name}")
    print(f"Age           : {age}")
    print(f"Track         : {track}")
    print(f"AI Eligible   : {'Python' in skills}")
    print(f"Needs Upskill : {need_upskilling}")
    if(len(skills) > 3 and experience > 5):
        print("Fast Track Candidate!")
    

#Ai generated
name = input("Enter your name: ").strip().title()
age = int(input("Enter your age: "))
experience = float(input("Enter your years of experience: "))
skills_input = input("Enter your skills (comma separated): ")
skills_list = [s.strip().title() for s in skills_input.split(",")]

# Determine track
if experience < 1:
    track = "Intern Track"
elif experience <= 3:
    track = "Junior Track"
elif experience <= 6:
    track = "Mid-Level Track"
else:
    track = "Senior Track"

# Notice period using match
match track:
    case "Intern Track":
        notice = "2 weeks"
    case "Junior Track":
        notice = "1 month"
    case "Mid-Level Track":
        notice = "2 months"
    case "Senior Track":
        notice = "3 months"
    case _:
        notice = "N/A"

has_python = "Python" in skills_list
needs_upskill = "No" if has_python else "Yes"

if age >= 18:
    print("===== Application Result =====")
    print(f"Name          : {name}")
    print(f"Age           : {age}")
    print(f"Track         : {track}")
    print(f"AI Eligible   : {has_python}")
    print(f"Notice Period : {notice}")
    print(f"Needs Upskill : {needs_upskill}")

    if len(skills_list) > 3 and experience >= 5:
        print("\n🚀 Fast Track Candidate!")
else:
    print("Sorry, you must be 18 or older to apply.")