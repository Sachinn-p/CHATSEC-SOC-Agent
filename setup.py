"""
Setup script for SOC Agent Automation.
"""
from setuptools import setup, find_packages
import os

# Read README.md for long description
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "SOC Agent Automation - MCP + Wazuh Chat with Dashboard & Proactive Agents"

# Read requirements from requirements.txt
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "streamlit>=1.28.0",
            "mcp-use>=0.1.0", 
            "langchain-groq>=0.1.0",
            "python-dotenv>=1.0.0",
            "apscheduler>=3.10.0",
            "pandas>=2.0.0",
        ]

setup(
    name="soc-agent-automation",
    version="1.0.0",
    author="SOC Team",
    author_email="soc@company.com",
    description="MCP + Wazuh Chat with Dashboard & Proactive Agents for SOC Automation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/company/soc-agent-automation",
    packages=find_packages(include=["src*", "config*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "soc-agent=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.json"],
    },
    zip_safe=False,
)