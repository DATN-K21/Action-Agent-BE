{{- define "aa.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "aa.fullname" -}}
{{- printf "%s-%s" .Release.Name (.Chart.Name | trunc 63 | trimSuffix "-") -}}
{{- end -}}

{{- define "aa.labels" -}}
app.kubernetes.io/name: {{ include "aa.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
{{- end -}}

{{- define "aa.image" -}}
{{- $registry := .root.Values.global.imageRegistry -}}
{{- $repository := .image.repository -}}
{{- $tag := .image.tag | default "latest" -}}
{{- if $registry }}{{ printf "%s/%s:%s" $registry $repository $tag }}{{ else }}{{ printf "%s:%s" $repository $tag }}{{ end }}
{{- end -}}
