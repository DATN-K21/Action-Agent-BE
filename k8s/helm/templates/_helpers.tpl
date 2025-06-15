{{- define "action-agent.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "action-agent.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "action-agent.image" -}}
{{- printf "%s/%s:%s" .root.Values.global.imageRegistry .repository .tag -}}
{{- end -}}

{{- define "action-agent.secretName" -}}
{{ printf "%s-%s" (include "action-agent.fullname" .root) .name }}
{{- end -}}
