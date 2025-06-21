import google.generativeai as genai
genai.configure(api_key="AIzaSyDqwDRZoLeaKog1R4oqMKYg8e42W0Blrjc")

model = genai.GenerativeModel("gemini-pro")
response = model.generate_content("Hello!")
print(response)
