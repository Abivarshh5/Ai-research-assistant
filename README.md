# 🔍 AI Research Assistant

An advanced, full-stack AI-powered research pipeline designed to transform complex topics into comprehensive, structured reports. Built with **LangGraph** orchestration, **CrewAI** agents, and a modern **React** frontend.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![React](https://img.shields.io/badge/Frontend-React%2019-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)

---

## 🚀 Key Features

- **Deep Research Pipeline**: Leverages specialized AI agents to crawl the web, analyze data, and synthesize information.
- **Iterative Refinement**: Refine reports in real-time through user feedback. Choose between *Analytical* and *Applied* variants.
- **Smart Orchestration**: Uses **LangGraph** to manage complex research workflows and state transitions.
- **Multi-Channel Delivery**:
  - 📧 **Email Integration**: Send generated reports directly via SendGrid.
  - 🔔 **Push Notifications**: Real-time status updates and delivery.
  - 📄 **PDF Export**: Generate clean, professional PDF versions of your research.
- **Modern UI**: A premium, minimalist interface built with Vite, Tailwind CSS, and Lucide icons.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Orchestration**: LangGraph, LangChain
- **Agent Framework**: CrewAI, PyAutoGen
- **Search & Scraping**: Playwright, BeautifulSoup4
- **Report Generation**: xhtml2pdf, Markdown
- **Delivery**: SendGrid API

### Frontend
- **Framework**: React 19 (Vite)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Markdown Rendering**: React Markdown, Remark GFM
- **PDF Generation**: html2pdf.js

---

## 📦 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys: OpenAI, SendGrid (optional)

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory and add your credentials:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   SENDGRID_API_KEY=your_sendgrid_key
   ```
5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

---

## 🏗️ Architecture

The project follows a modular architecture where the **LangGraph** engine coordinates multiple AI agents (Researcher, Writer, Reviewer) to ensure high-quality output. The frontend communicates with the backend via **WebSockets** for real-time status streaming and **REST APIs** for report management.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Developed with ❤️ by [Abivarshh](https://github.com/Abivarshh5)
