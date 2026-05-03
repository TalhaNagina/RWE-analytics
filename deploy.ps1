# Cloud Run Deployment Script for OphthoRWE Platform (Windows)
# YellowSense Technologies

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "OphthoRWE Platform - Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_ID = "yellowsense-technologies"  # CHANGE THIS
$SERVICE_NAME = "ophtho-rwe-platform"
$REGION = "asia-south1"  # Change if needed
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Project ID: $PROJECT_ID"
Write-Host "  Service Name: $SERVICE_NAME"
Write-Host "  Region: $REGION"
Write-Host ""

# Check if gcloud is installed
try {
    $gcloudVersion = gcloud version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud not found"
    }
} catch {
    Write-Host "❌ Error: gcloud CLI is not installed" -ForegroundColor Red
    Write-Host "Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Check authentication
Write-Host "Checking authentication..." -ForegroundColor Yellow
$authList = gcloud auth list --filter=status:ACTIVE --format="value(account)"
if ([string]::IsNullOrEmpty($authList)) {
    Write-Host "❌ Not authenticated. Running gcloud auth login..." -ForegroundColor Red
    gcloud auth login
}

# Set project
Write-Host ""
Write-Host "Setting project to $PROJECT_ID..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host ""
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the container
Write-Host ""
Write-Host "Building Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build successful!" -ForegroundColor Green

# Deploy to Cloud Run
Write-Host ""
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --set-env-vars "STREAMLIT_SERVER_HEADLESS=true,STREAMLIT_SERVER_PORT=8080"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

# Get the service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "✅ Deployment Successful!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Service URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 View logs:" -ForegroundColor Yellow
Write-Host "   gcloud run logs read $SERVICE_NAME --region $REGION --limit 50"
Write-Host ""
Write-Host "🔍 View service details:" -ForegroundColor Yellow
Write-Host "   gcloud run services describe $SERVICE_NAME --region $REGION"
Write-Host ""
Write-Host "🗑️  Delete service:" -ForegroundColor Yellow
Write-Host "   gcloud run services delete $SERVICE_NAME --region $REGION"
Write-Host ""
Write-Host "==================================" -ForegroundColor Green