from setuptools import setup, find_packages

setup(
    name="rubber-ducky",
    version="0.1.0",
    description="Local voice conversation system with WhisperX, Coqui XTTS v2, and configurable LLMs",
    author="Troy Daniel",
    author_email="troygdaniel@gmail.com",
    packages=find_packages(),
    install_requires=[
        "torch>=2.2.0",
        "whisperx>=3.1.0",
        "coqui-tts>=0.27.5",
        "anthropic>=0.34.0",
        "httpx>=0.27.0",
        "sounddevice>=0.4.6",
        "numpy>=1.26.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.5.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
        "sqlalchemy>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "rubber-ducky=rubber_ducky.cli.commands:cli",
        ],
    },
    python_requires=">=3.10,<3.15",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
