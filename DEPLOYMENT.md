# Deployment Guide for Render

This guide explains how to deploy the Financial Analysis Web Application to Render.

## Prerequisites

- A GitHub repository containing your application code
- A Render account (free tier available)

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository contains these files:
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `start.sh` - Startup script (optional, render.yaml handles this)
- `.env.example` - Environment variables template

### 2. Deploy to Render

#### Option A: Using render.yaml (Recommended)

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` file and configure the service

#### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the following settings:
   - **Name**: `financial-analysis-app`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Plan**: `Free` (or your preferred plan)

### 3. Environment Variables

Set these environment variables in Render:

- `FLASK_ENV`: `production`
- `SECRET_KEY`: Generate a secure random key
- `CACHE_TIMEOUT`: `900`
- `LOG_LEVEL`: `WARNING`

### 4. Custom Domain (Optional)

If you have a custom domain:
1. Go to your service settings
2. Add your custom domain
3. Configure DNS records as instructed by Render

## Application Features

The deployed application includes:
- Stock analysis with Eight Pillars scoring
- Portfolio management and optimization
- Interactive charts and visualizations
- Recent analyses tracking with session storage
- Responsive design for mobile and desktop

## Environment Configuration

The application automatically detects the environment and adjusts settings:
- **Development**: Debug mode enabled, detailed logging
- **Production**: Optimized for performance, minimal logging

## Troubleshooting

### Common Issues

1. **Build Failures**: Check that all dependencies in `requirements.txt` are correct
2. **Start Failures**: Ensure the start command matches your application structure
3. **Environment Variables**: Verify all required environment variables are set

### Logs

View application logs in the Render dashboard:
1. Go to your service
2. Click on "Logs" tab
3. Monitor for any errors or issues

## Support

For deployment issues:
- Check Render documentation: https://render.com/docs
- Review application logs in Render dashboard
- Ensure all dependencies are properly specified

## Security Notes

- Never commit sensitive data like API keys or secret keys
- Use environment variables for all configuration
- The application uses secure session management
- HTTPS is automatically provided by Render