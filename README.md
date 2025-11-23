# 🧠 Study Planner Agent

A simple AI-powered Study Planner Agent that generates a personalized study schedule from your subjects, available hours per day, and start date.  
This project was built as part of my **Capstone AI Agent Project**.

---

## 🚀 Features

- Input your subjects and available hours  
- Automatically generates a structured day-by-day study plan  
- FastAPI backend with a scheduling algorithm  
- Simple React-based frontend  
- Export or fetch your plan anytime  
- Easy to run locally  

---

## 🏗️ Project Structure


---

## ⚙️ How to Run the Backend (FastAPI)

### 1. Open terminal and navigate to the backend folder:


### 2. Create a virtual environment (optional but recommended):


### 3. Install dependencies:


### 4. Start the FastAPI server:


Your backend will now be running at:

👉 http://127.0.0.1:8000  
👉 Interactive docs: http://127.0.0.1:8000/docs

---

## 🖥️ How to Run the Frontend (React)

You can use any simple React setup.

### 1. Create a new React app:


### 2. Replace the default `src/App.js` with the `frontend/App.jsx` from this repo.

### 3. Start the frontend:


---

## 📡 API Endpoints Overview

| Method | Endpoint          | Description |
|--------|------------------|-------------|
| POST   | `/create-plan`   | Create a new study plan |
| GET    | `/get-plan`      | Fetch an existing plan |
| POST   | `/update-progress` | Mark a session done/skipped |
| GET    | `/export`        | Export a full study plan |

---

## 🎥 Demo Video Script (for capstone)

1. Show your GitHub project repo  
2. Run backend with FastAPI  
3. Open frontend and create a study plan  
4. Show API documentation in `/docs`  
5. Demonstrate the generated schedule  
6. End with a quick explanation of how the agent helps students  

---

## 🏁 Capstone Summary

This agent helps students generate a personalized study plan based on subjects, difficulty, and daily available time.  
It showcases:

- AI Agent design  
- Backend API development  
- Simple UI integration  
- Automation and scheduling logic  

---

## 📄 License

MIT License – free to use and modify.
