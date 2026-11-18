# Template Helm Chart

TODO: **Update this file to be relevant to your application**

The helm chart in this directory will fully deploy this application
to the desired environment. Currently there are two, test and prod.

Check the [values.yaml](values.yaml) for settings documentationand the [upstream helm chart](https://charts.example.com/demo)as well as the [application documentation](https://github.com/example/demo)
documentation for details.

All files in the [templates](templates) subdirectory will be rendered
as Helm templates. [templates/_common.tpl](templates/_common.tpl)
includes common functions that can and should be used in all templates.

## Required Parts of Each Template

Each Kubernetes resource must be able to be tied back to the Helm
app so that Helm can keep track of it. Therefore, _any time that
labels are defined, common labels should be included_, like this:
```yaml
---
apiVersion: some-group.tld/vX
kind: SomeKind
metadata:
  name: {{ $name }}-thing
  labels:
    {{- include "common.labels" $ | nindent 4 }}
spec:
    ...
```

The key element there is the line `{{- include "common.labels" $ | nindent 4 }}`
which says include the string generated when `common.labels` is passed
the root of the Values (`$`), and indent it by 4 while prepending a newline to the
start of thes string ([nindent](https://helm.sh/docs/chart_template_guide/function_list/#nindent)).

The above example is fairly trivial, a `Deployment` might have 3 different places
labels are applied and _each one_ must add the common labels. You can see
what those are by checking the [temlates/_common.tpl](templates/_common.tpl)
file.

## Useful Common Functions

`common.names.chart`: Resolves to the chart name and version and should be used anywhere
a unique identification of the chart throughout the cluster is needed.

`common.names.name`: Resolves to the chart name and can be overriden by `global.nameOverride`.

`common.labels`: Resolves to all required labels.

`common.labels.selectorLabels`: Resolves to common labels used in selectors to help when
tying objects together using selectors. This is useful when defining services. Use
`{{- include "common.labels.selectorLabels" $ | nindent X }}` in _both_ the
`Deployment`'s `PodSpec` and the `Service`'s selectors and watch magic happen.

## Persistent Volumes

Helm both creates and deletes resources it deploys, it may also delete resources on upgrade
if something is different. This can be **very bad** for persistent volumes as deleting
a PVC will often delete the underlying PV which will trigger deletion of the underlying
data. To avoid this, all persistent volumes should be annotated with
`helm.sh/resource-policy: keep` to prevent Helm from deleting them ever. For example:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
    name: example-claim
    annotations:
        helm.sh/resource-policy: keep
    labels:
        {{- include "common.labels" $ | nindent 4 }}
spec:
    accessModes:
    - ReadWriteOnce
    resources:
        requests:
            storage: 1Mi
    storageClassName: ohio-rwo-block-distributed
```
