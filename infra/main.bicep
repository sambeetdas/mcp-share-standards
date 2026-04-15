// MCP Enterprise Standards Server — Azure App Service deployment
// Deploys: ACR + App Service Plan (Linux) + Web App for Containers

targetScope = 'resourceGroup'

@description('Base name used for all resources')
param appName string = 'mcp-standards'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('SKU for the App Service Plan')
@allowed(['B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1v3', 'P2v3', 'P3v3'])
param appServiceSkuName string = 'B1'

@description('SKU for Azure Container Registry')
@allowed(['Basic', 'Standard', 'Premium'])
param acrSku string = 'Basic'

@description('Docker image tag to deploy')
param imageTag string = 'latest'

// Sanitize names for Azure naming rules
var sanitizedName = replace(toLower(appName), '-', '')
var uniqueSuffix = uniqueString(resourceGroup().id)
var acrName = '${sanitizedName}acr${take(uniqueSuffix, 5)}'
var appServicePlanName = '${appName}-plan'
var webAppName = '${appName}-app'
var imageName = 'mcp-standards-server'

// Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: acrSku
  }
  properties: {
    adminUserEnabled: true
  }
}

// App Service Plan (Linux)
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'
  sku: {
    name: appServiceSkuName
  }
  properties: {
    reserved: true
  }
}

// Web App for Containers
resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  kind: 'app,linux,container'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${acr.properties.loginServer}/${imageName}:${imageTag}'
      alwaysOn: true
      appSettings: [
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${acr.properties.loginServer}'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_USERNAME'
          value: acr.listCredentials().username
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_PASSWORD'
          value: acr.listCredentials().passwords[0].value
        }
        {
          name: 'WEBSITES_PORT'
          value: '8080'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'MCP_ALLOWED_HOSTS'
          value: '${webAppName}.azurewebsites.net'
        }
      ]
    }
  }
}

// Outputs
output acrLoginServer string = acr.properties.loginServer
output acrName string = acr.name
output webAppName string = webApp.name
output webAppHostName string = webApp.properties.defaultHostName
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
