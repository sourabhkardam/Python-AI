original_name = input("Enter your full name: ")
title_name = original_name.strip().title()
skills_string = input("Enter skills in comma separated format: ")
skills_list = skills_string.strip().split(",")
full_name = original_name.split(" ")

print("==== String Analysis")
print(f"Original Name           : {original_name}")
print(f"Name in Upper Case      : {original_name.upper()}")
print(f"Name in Lower Case      : {original_name.lower()}")
print(f"Name with Title         : {title_name}")
print(f"Number of Character     : {len(title_name)}")
print(f"{full_name[0]}.{full_name[1]}.")

print("===== Skills =====")
print(f"Skills          : {skills_list}")
print(f"Total           : {len(skills_list)}")
print(f"Has Python      : {'Python' in skills_list}")
print(f"Formatted       : {' | '.join(skills_list)}")

#Ai generated
original_name = input("Enter your full name: ")
title_name = original_name.strip().title()
skills_string = input("Enter skills in comma separated format: ")
skills_list = [skill.strip().title() for skill in skills_string.split(",")]
full_name = title_name.split(" ")

print("===== String Analysis =====")
print(f"Original  : {title_name}")
print(f"Upper     : {title_name.upper()}")
print(f"Lower     : {title_name.lower()}")
print(f"Length    : {len(title_name)}")
print(f"Initials  : {full_name[0][0]}.{full_name[1][0]}.")

print("\n===== Skills =====")
print(f"Skills    : {skills_list}")
print(f"Total     : {len(skills_list)}")
print(f"Has Python: {'Python' in skills_list}")
print(f"Formatted : {' | '.join(skills_list)}")

print("\n===== Bonus =====")
print(f"Starts with vowel: {title_name[0].lower() in 'aeiou'}")
