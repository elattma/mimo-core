import { RemovalPolicy, Stack, StackProps } from "aws-cdk-lib";
import { AttributeType, BillingMode, Table } from "aws-cdk-lib/aws-dynamodb";
import { Construct } from "constructs";

export interface DynamoStackProps extends StackProps {
  readonly stageId: string;
}

export class DynamoStack extends Stack {
  readonly mimoTable: Table;
  readonly waitlistTable: Table;

  constructor(scope: Construct, id: string, props: DynamoStackProps) {
    super(scope, id, props);

    this.mimoTable = new Table(this, `mimo-${props.stageId}-pc-ddb`, {
      partitionKey: {
        name: "parent",
        type: AttributeType.STRING,
      },
      sortKey: {
        name: "child",
        type: AttributeType.STRING,
      },
      pointInTimeRecovery: true,
      tableName: `mimo-${props.stageId}-pc`,
      removalPolicy: RemovalPolicy.RETAIN,
      billingMode: BillingMode.PAY_PER_REQUEST,
    });
    this.mimoTable.addGlobalSecondaryIndex({
      indexName: "child-index",
      partitionKey: {
        name: "child",
        type: AttributeType.STRING,
      },
    });

    this.waitlistTable = new Table(this, `mimo-${props.stageId}-waitlist`, {
      partitionKey: {
        name: "email",
        type: AttributeType.STRING,
      },
      pointInTimeRecovery: true,
      tableName: `mimo-${props.stageId}-waitlist`,
      removalPolicy: RemovalPolicy.RETAIN,
      billingMode: BillingMode.PAY_PER_REQUEST,
    });
  }
}
