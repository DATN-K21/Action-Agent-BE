# Helm template helpers
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
Usage: {{ include "action-agent.secretName" (dict "root" . "name" "user-db") }}
*/}}
{{- define "action-agent.secretName" -}}
{{- printf "%s-%s-secret" (include "action-agent.fullname" .root) .name }}
{{- end }}

{{/*
Generate configmap name for a service
Usage: {{ include "action-agent.configMapName" (dict "root" . "name" "service-name") }}
*/}}
{{- define "action-agent.configMapName" -}}
{{- printf "%s-%s-config" (include "action-agent.fullname" .root) .name }}
{{- end }}

{{/*
Generate service name
Usage: {{ include "action-agent.serviceName" (dict "root" . "name" "service-name") }}
*/}}
{{- define "action-agent.serviceName" -}}
{{- printf "%s-%s" (include "action-agent.fullname" .root) .name }}
{{- end }}

{{/*
Generate database connection string for MongoDB
*/}}
{{- define "action-agent.mongoConnectionString" -}}
{{- $host := printf "%s-%s" (include "action-agent.fullname" .) "user-database" }}
{{- printf "mongodb://%s:%s@%s:27017/%s?authSource=admin" .Values.userService.database.username .Values.userService.database.password $host .Values.userService.database.name }}
{{- end }}

{{/*
Generate database connection string for PostgreSQL
*/}}
{{- define "action-agent.postgresConnectionString" -}}
{{- $host := printf "%s-%s" (include "action-agent.fullname" .) "ai-database" }}
{{- printf "postgresql://%s:%s@%s:5432/%s" .Values.aiService.database.username .Values.aiService.database.password $host .Values.aiService.database.name }}
{{- end }}
