targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the environment, used to derive resource names. Set via `azd env new <name>`.')
param environmentName string

@description('Primary Azure region for App Service, App Insights, and Bot.')
param location string = resourceGroup().location

@description('Microsoft Entra tenant id for the Bot app registration.')
param botTenantId string = subscription().tenantId

@description('App (client) id of the Microsoft Entra app registration backing the Bot.')
param botAppId string

@description('Client secret of the Microsoft Entra app registration backing the Bot.')
@secure()
param botAppSecret string

@description('Endpoint of the Microsoft Foundry project. e.g. https://<proj>.services.ai.azure.com/api/projects/<proj>')
param foundryProjectEndpoint string

@description('Name of the chat model deployment inside the Foundry project (e.g. gpt-4o-mini).')
param foundryModelDeployment string = 'gpt-4o-mini'

@description('Resource id of the Microsoft Foundry account (Cognitive Services account) hosting the project. Used to assign RBAC to the agent identity.')
param foundryAccountResourceId string = ''

var tags = {
  'azd-env-name': environmentName
  purpose: 'demo'
  owner: 'gbelenky'
  workload: 'streaming-teams-agent'
}

var resourceToken = uniqueString(subscription().id, resourceGroup().id, environmentName)
var planName = 'asp-${resourceToken}'
var siteName = 'app-${resourceToken}'
var aiName = 'appi-${resourceToken}'
var lawName = 'log-${resourceToken}'
var botName = 'bot-${resourceToken}'
var uamiName = 'id-${resourceToken}'

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: uamiName
  location: location
  tags: tags
}

resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: lawName
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource ai 'Microsoft.Insights/components@2020-02-02' = {
  name: aiName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: planName
  location: location
  tags: tags
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource site 'Microsoft.Web/sites@2024-04-01' = {
  name: siteName
  location: location
  tags: union(tags, { 'azd-service-name': 'api' })
  kind: 'app,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    keyVaultReferenceIdentity: uami.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      appCommandLine: 'python -m streaming_teams_agent'
      appSettings: [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'WEBSITES_PORT'
          value: '3978'
        }
        {
          name: 'PORT'
          value: '3978'
        }
        {
          name: 'HOST'
          value: '0.0.0.0'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: ai.properties.ConnectionString
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: uami.properties.clientId
        }
        {
          name: 'FOUNDRY_PROJECT_ENDPOINT'
          value: foundryProjectEndpoint
        }
        {
          name: 'FOUNDRY_MODEL_DEPLOYMENT'
          value: foundryModelDeployment
        }
        {
          name: 'CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID'
          value: botAppId
        }
        {
          name: 'CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET'
          value: botAppSecret
        }
        {
          name: 'CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID'
          value: botTenantId
        }
      ]
    }
  }
}

resource bot 'Microsoft.BotService/botServices@2022-09-15' = {
  name: botName
  location: 'global'
  tags: tags
  kind: 'azurebot'
  sku: {
    name: 'F0'
  }
  properties: {
    displayName: botName
    endpoint: 'https://${site.properties.defaultHostName}/api/messages'
    msaAppId: botAppId
    msaAppType: 'SingleTenant'
    msaAppTenantId: botTenantId
    developerAppInsightKey: ai.properties.InstrumentationKey
    developerAppInsightsApplicationId: ai.properties.AppId
  }
}

resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = {
  parent: bot
  name: 'MsTeamsChannel'
  location: 'global'
  properties: {
    channelName: 'MsTeamsChannel'
    properties: {
      isEnabled: true
    }
  }
}

var foundryRgName = !empty(foundryAccountResourceId) ? split(foundryAccountResourceId, '/')[4] : resourceGroup().name
var foundryAccountName = !empty(foundryAccountResourceId) ? last(split(foundryAccountResourceId, '/')) : ''

module foundryRbac 'modules/foundry-rbac.bicep' = if (!empty(foundryAccountResourceId)) {
  name: 'foundry-rbac'
  scope: resourceGroup(foundryRgName)
  params: {
    foundryAccountName: foundryAccountName
    principalId: uami.properties.principalId
  }
}

output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = resourceGroup().name
output SERVICE_API_NAME string = site.name
output SERVICE_API_URI string = 'https://${site.properties.defaultHostName}'
output BOT_NAME string = bot.name
output BOT_ENDPOINT string = 'https://${site.properties.defaultHostName}/api/messages'
output APPLICATIONINSIGHTS_CONNECTION_STRING string = ai.properties.ConnectionString
output AGENT_MANAGED_IDENTITY_CLIENT_ID string = uami.properties.clientId
