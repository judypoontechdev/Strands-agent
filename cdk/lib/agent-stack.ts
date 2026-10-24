import * as dotenv from "dotenv";
import * as path from "path";
import { Stack, StackProps, Duration } from "aws-cdk-lib";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { PolicyStatement, Effect } from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";

// load env
dotenv.config({ path: path.join(__dirname, "../../.env") });

export class AgentStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // defines an AWS Lambda resource
    const agent = new PythonFunction(this, "AgentHandler", {
      entry: "../src", // code loaded from "src" directory
      runtime: Runtime.PYTHON_3_11, // execution environment
      index: "lambda_handler.py", // file is "lambda_handler"
      handler: "lambda_handler", // function is "lambda_handler"
      timeout: Duration.seconds(120),
      memorySize: 512,
      environment: {
        REST_COUNTRIES_API_KEY: process.env.REST_COUNTRIES_API_KEY || "",
      },
    });

    agent.addToRolePolicy(
      new PolicyStatement({
        effect: Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      }),
    );
  }
}
