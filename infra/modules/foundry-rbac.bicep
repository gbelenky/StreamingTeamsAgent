targetScope = 'resourceGroup'

@description('Name of the Foundry (Cognitive Services) account in the target resource group.')
param foundryAccountName string

@description('Principal id (object id) of the managed identity to grant Azure AI User on the Foundry account.')
param principalId string

var azureAIUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: foundryAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccount.id, principalId, azureAIUserRoleId)
  scope: foundryAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAIUserRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
