{{/*
Expand the name of the chart.
*/}}
{{- define "action-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "action-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "action-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "action-agent.labels" -}}
helm.sh/chart: {{ include "action-agent.chart" . }}
{{ include "action-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
environment: {{ .Values.global.environment }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "action-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "action-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "action-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "action-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate secret name for a service
*/}}
{{- define "action-agent.secretName" -}}
{{- printf "%s-%s-secret" (include "action-agent.fullname" .root) .service }}
{{- end }}

{{/*
Generate image tag
*/}}
{{- define "action-agent.imageTag" -}}
{{- if .tag }}
{{- .tag }}
{{- else }}
{{- .root.Values.global.imageTag | default "latest" }}
{{- end }}
{{- end }}

{{/*
Generate full image name
*/}}
{{- define "action-agent.image" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .repository (include "action-agent.imageTag" .) }}
{{- else }}
{{- printf "%s:%s" .repository (include "action-agent.imageTag" .) }}
{{- end }}
{{- end }}

{{/*
Generate userDatabase connection string
*/}}
{{- define "action-agent.userDatabaseConnectionString" -}}
{{- if .Values.external.userDatabase.enabled }}
{{- .Values.external.userDatabase.connectionString }}
{{- else }}
{{- printf "mongodb://%s:%s@%s-user-db:27017/%s?authSource=%s" .Values.databases.userDatabase.auth.username .Values.databases.userDatabase.auth.password (include "action-agent.fullname" .) .Values.databases.userDatabase.database .Values.databases.userDatabase.database }}
{{- end }}
{{- end }}

{{/*
Generate extensionDatabase connection string
*/}}
{{- define "action-agent.extensionDatabaseConnectionString" -}}
{{- if .Values.external.extensionDatabase.enabled }}
{{- .Values.external.extensionDatabase.connectionString }}
{{- else }}
{{- printf "mongodb://%s:%s@%s-extension-db:27017/%s?authSource=%s" .Values.databases.extensionDatabase.auth.username .Values.databases.extensionDatabase.auth.password (include "action-agent.fullname" .) .Values.databases.extensionDatabase.database .Values.databases.extensionDatabase.database }}
{{- end }}
{{- end }}

{{/*
Generate aiDatabase connection string
*/}}
{{- define "action-agent.aiDatabaseConnectionString" -}}
{{- if .Values.external.aiDatabase.enabled }}
{{- .Values.external.aiDatabase.connectionString }}
{{- else }}
{{- printf "postgresql://%s:%s@%s-ai-db:5432/%s" .Values.databases.aiDatabase.auth.username .Values.databases.aiDatabase.auth.password (include "action-agent.fullname" .) .Values.databases.aiDatabase.database }}
{{- end }}
{{- end }}

{{/*
Generate Redis connection string
*/}}
{{- define "action-agent.redisConnectionString" -}}
{{- if .Values.external.redis.enabled }}
{{- .Values.external.redis.connectionString }}
{{- else }}
{{- if .Values.databases.redis.auth.password }}
{{- printf "redis://:%s@%s-redis:6379" .Values.databases.redis.auth.password (include "action-agent.fullname" .) }}
{{- else }}
{{- printf "redis://%s-redis:6379" (include "action-agent.fullname" .) }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Check if we should create internal databases
*/}}
{{- define "action-agent.createInternalDatabases" -}}
{{- and (not .Values.external.mongodb.enabled) (not .Values.external.postgresql.enabled) }}
{{- end }}

{{/*
Check if we should create internal infrastructure
*/}}
{{- define "action-agent.createInternalInfrastructure" -}}
{{- and (not .Values.external.elasticsearch.enabled) (not .Values.external.rabbitmq.enabled) }}
{{- end }}
