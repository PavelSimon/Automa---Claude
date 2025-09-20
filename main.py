def main():
    """Main entry point for the Automa application."""
    import uvicorn

    print("Starting Automa - Python Agent Management Platform")
    print("Using uv for dependency management")
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )


if __name__ == "__main__":
    main()
