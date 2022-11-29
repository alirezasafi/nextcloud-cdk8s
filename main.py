#!/usr/bin/env python
from constructs import Construct
from cdk8s import App, Chart

from imports import k8s

class MyChart(Chart):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        
        # global vars
        app: str = "nextcloud"
        image: str = "nextcloud:apache"
        pod_replicas: int = 1
        pvc_name: str = f"{app}-data"
        pvc_storage_size: str = "100Mi"
        pvc_storage_class_name: str = "rawfile-btrfs"
        datadir: str = "/var/www/html/data"

        # define resources here
        labels: dict  = {"app": app}

        ##### Service
        k8s.KubeService(
            self, 'service',
            metadata=k8s.ObjectMeta(
                name=f"{app}-svc",
                labels=labels
            ),
            spec=k8s.ServiceSpec(
                type='LoadBalancer',
                ports=[
                    k8s.ServicePort(port=80, target_port=k8s.IntOrString.from_string('http'), protocol='TCP')
                ],
                selector=labels
            )
        )
        
        ##### PVC
        k8s.KubePersistentVolumeClaim(
            self, 'persistentvolumeclaim',
            metadata=k8s.ObjectMeta(
                name=pvc_name,
                labels=labels
            ),
            spec=k8s.PersistentVolumeClaimSpec(
                resources=k8s.ResourceRequirements(
                    requests={"storage": k8s.Quantity.from_string(pvc_storage_size)}
                ),
                storage_class_name=pvc_storage_class_name,
                access_modes=[
                    "ReadWriteOnce"
                ]
            )
        )
        
        ##### Deployment
        k8s.KubeDeployment(
            self, 'deployment',
            metadata=k8s.ObjectMeta(
                name=f"{app}-dep",
                labels=labels   
            ),
            spec=k8s.DeploymentSpec(
                replicas=pod_replicas,
                strategy=k8s.DeploymentStrategy(type="Recreate"),
                selector=k8s.LabelSelector(match_labels=labels),
                template=k8s.PodTemplateSpec(
                    metadata=k8s.ObjectMeta(labels=labels),
                    spec=k8s.PodSpec(
                        volumes=[
                            k8s.Volume(
                                name=pvc_name,
                                persistent_volume_claim=k8s.PersistentVolumeClaimVolumeSource(claim_name=pvc_name)
                            )
                        ],
                        containers=[
                            k8s.Container(
                                name=app,
                                image=image,
                                image_pull_policy="IfNotPresent",
                                ports=[
                                    k8s.ContainerPort(name="http", container_port=80, protocol="TCP")
                                ],
                                resources=k8s.ResourceRequirements(
                                    limits={"cpu": k8s.Quantity.from_string("1"), "memory": k8s.Quantity.from_string("1Gi")},
                                    requests={"cpu": k8s.Quantity.from_string("1"), "memory": k8s.Quantity.from_string("1Gi")}
                                ),
                                volume_mounts=[
                                    k8s.VolumeMount(name=pvc_name, mount_path=datadir)
                                ]
                            ),
                            k8s.Container(
                                name=f"{app}-cron",
                                image=image,
                                image_pull_policy="IfNotPresent",
                                command=["/cron.sh"],
                                resources=k8s.ResourceRequirements(
                                    limits={"cpu": k8s.Quantity.from_string("100m"), "memory": k8s.Quantity.from_string("128Mi")},
                                    requests={"cpu": k8s.Quantity.from_string("100m"), "memory": k8s.Quantity.from_string("128Mi")}
                                )
                            )
                        ]
                    )
                )
            )
        )
        


app = App()
MyChart(app, "nextcloud-cdk8s")

app.synth()
