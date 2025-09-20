def main():
    """Main entry point for the Automa application."""
    import uvicorn
    from backend.app.main import app

    print("Starting Automa - Python Agent Management Platform")
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()
