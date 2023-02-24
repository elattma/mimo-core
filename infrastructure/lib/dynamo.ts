import { RemovalPolicy, Stack, StackProps } from "aws-cdk-lib";
import { AttributeType, BillingMode, Table } from "aws-cdk-lib/aws-dynamodb";
import { Construct } from "constructs";

export class DynamoStack extends Stack {
  public readonly mimoTable: Table;

  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    this.mimoTable = new Table(this, "mimo-pc-ddb", {
      partitionKey: {
        name: "parent",
        type: AttributeType.STRING,
      },
      sortKey: {
        name: "child",
        type: AttributeType.STRING,
      },
      pointInTimeRecovery: true,
      tableName: "mimo-beta-pc",
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
  }
}
