// import { Stack, StackProps } from "aws-cdk-lib";
// import { IVpc } from "aws-cdk-lib/aws-ec2";
// import { Cluster } from "aws-cdk-lib/aws-eks";
// import { LogGroup, RetentionDays } from "aws-cdk-lib/aws-logs";
// import { Choice, Condition, StateMachine } from "aws-cdk-lib/aws-stepfunctions";
// import { EksCall, HttpMethods } from "aws-cdk-lib/aws-stepfunctions-tasks";
// import { Construct } from "constructs";
// import path = require("path");

// export interface StateStackProps extends StackProps {
//   readonly stageId: string;
//   readonly vpc: IVpc;
// }

// export class StateStack extends Stack {
//   constructor(scope: Construct, id: string, props: StateStackProps) {
//     super(scope, id, props);

//     const clusterName = process.env.CLUSTER_NAME || "";
//     const clusterEndpoint = process.env.CLUSTER_ENDPOINT;
//     const clusterCertificateAuthorityData = process.env.CLUSTER_CAD;
//     const airbyte = Cluster.fromClusterAttributes(this, "airbyte-cluster", {
//       clusterName: clusterName,
//       clusterEndpoint: clusterEndpoint,
//       clusterCertificateAuthorityData: clusterCertificateAuthorityData,
//     });

//     const airbyteIngestJob = new EksCall(this, "airbyte-ingest-job", {
//       cluster: airbyte,
//       httpMethod: HttpMethods.POST,
//       httpPath: "/api/v1/connections/sync",
//       requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
//     });

//     new StateMachine(this, "create-connection", {
//       definition: paramsJob.next(
//         new Choice(this, "Airbyte or Batch?")
//           .when(
//             Condition.stringEquals("$.params.ingestion", "airbyte"),
//             airbyteIngestJob
//           )
//           .otherwise(ingestJob)
//       ),
//       logs: {
//         destination: new LogGroup(this, "mimo-cc-logs", {
//           logGroupName: `mimo-${props.stageId}-cc-logs`,
//           retention: RetentionDays.ONE_WEEK,
//         }),
//       },
//     });
//   }
// }
