# SSO with Amazon Lambda

## What's this

A single sign on app to demonstrate [Amazon Lambda](https://aws.amazon.com/lambda/details/) service. Those products are used in this demo:

* Amazon Lambda
* Amazon ApiGateway
* Amazon DynamoDB
* Google App

This app is running on Amazon Lambda platform, the API is exported via ApiGateway, while data is stored in DynamoDB. No extra EC2 instance needed.


## How to setup

Setup contains Amazon , Google and local parts, please refer to the instructions below.

### Amazon services

This app requires permission for three Amazon components:

* Lambda
* ApiGateway
* DynamoDB

Besides those components, please make sure there is existing IAM role can run Lambda with DynamoDB, or you need to create one, which requires IAM role. The Lambda functions put log into CloudWatch, please also make sure it is existing in your permission list.

#### Amazon Lambda

This apps currently requires 4 functions, which are:

* `SSO` - Main entry for Single Sign On
* `EmailSignin` - Sign in with email and password
* `GoogleOAuthSignin` - Sign in with google account
* `Signout` - Sign out

All those functions need ApiGateway association and DynamoDB permission. Special configuration for ApiGateway will be shown in next section.

#### Amazon ApiGateway

**tl;dr**

Here are the mapping configured for APIs used in SSO.

* `SSO`
  * *Method Request*: Add `Cookie` in *HTTP Request Headers* section.
  * *Integration Request*: Add `Cookie` and `atoken` in *application/json* section of *Body Mapping Templates*.
* `EmailSignup`
  * *Method Request*: Add `email` and `password` in *URL Query String Parameters*.
  * *Integration Request*: Add `email` and `password` in *application/json* part of *Body Mapping Templates* section.
  * *Integration Response*: Add `Set-Cookie` in *Header Mappings* section, and set its value to `integration.response.body.cookie`.
  * *Integration Response*: Add needed field in *application/json* part of *Body Mappings Templates* section.
* `GoogleOAuthSignin`
  * *Method Request*: Add `state` and `code` in *URL Query String Parameters*.
  * *Integration Request*: Add `state` and `code` in *application/json* part of *Body Mapping Templates* section.
  * *Integration Response*: Add `Set-Cookie` in *Header Mappings* section, and add needed field in *application/json* part of *Body Mappings Templates* section.
* `Signout`
  * *Method Request*: Add `Cookie` in *HTTP Request Headers* section.
  * *Integration Request*: Add `Cookie` and `atoken` in *application/json* section of *Body Mapping Templates*.
  * *Integration Response*: Add `Set-Cookie` in *Header Mappings* section, and set its value to `integration.response.body.cookie`.
  * *Integration Response*: Add needed field in *application/json* part of *Body Mappings Templates* section.


**Full Version**

Functions created in Lambda service can't be accessed until assigned trigger, and ApiGateway is one type of trigger. There are two ways to associate ApiGateway to Lambda functions. One is associate it while creating Lambda function, the other is create gateway in ApiGateway console and fill Lambda function name in. The second method may not show the ApiGateway associated in Lambda trigger panel, but no error while using it.

Besides providing input/output interfaces for Lambda functions, ApiGateway also responsible to map and filter input data to Lambda functions and generate correct response from data returned. The *tl;dr* version listed out all mappings needed for this demo, and there will be some more instructions in the full version.

The general process for making request and getting response with ApiGateway and Lambda is:

1. ApiGateway receive API request, and convert request headers and data to Lambda based on predefined request rules.
1. Lambda function get the data in key-value format.
1. Lambda process data with its logic, and return String or key-value format data.
1. ApiGateway format Lambda data with pre-defined response rules.

From the process we can see that Lambda function only contains logic of the code. In Python environment, Lambda functions only accept Python Dict object as input params, and return basic Python data type, such as String and Dict. While ApiGateway parses those returned data, then builds HTTP response based on pre defined rules. If no mappings are set in *response* scope, the data returned from Lambda function will be directly send to user. However, if no mappings in *request* scope, **NO** data will be passed.

### Google app

Google app here is used for SNS login here. There is no webpage for login with google, just fill your google appid and callback URL into this URL template:

```
https://accounts.google.com/o/oauth2/v2/auth?scope=email%20profile&state=<Your State>&redirect_uri=<ApiGateway callback>&response_type=code&client_id=<ClientID>
```

While accessing that URL, google will ask for email and password, then show the permission list requested. After giving the permission, Google will pass code to the callback URL, which is handled by Lambda. Please refer code for more detail.

### Local environment

This app is written in Python, and the supported version of Amazon Lambda is Python 2.7.

> Not all project needs local dev environment, but not for this project. I will describe differences later.

We will use *virtualenv* to setup local dev environment. Here are the commands, please replace `${TOP}` to your project directory.

```
$ cd ${TOP}
$ virtualenv .lambda_venv -p `which python2.7`
$ . ./.lambda_venv/bin/active
$ pip install -r requirements.txt
```

> This local env is **NOT** used for running services in local but only used for building packages. That's the reason why not all project needs local env. For those project that contains single file can be edited by Lambda built-in online editor.

After local env ready, we can deploy our code to Lambda service. There is a sample Makefile shipped inside, which can build deployment package and upload to AWS with cli tool. Before using this, please follow [this guide](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-set-up.html) to setup your local AWS cli tool, also you need to create and configure Lambda function from Amazon web UI, then update the function name in Makefile. After those done, you can use `make` command to deploy Lambda functions.

> NOTICE: This Makefile doesn't configure ApiGateway, please configure is manually with instructions above.


After function deployed, you can try using those functions by accessing the Google login address. After given permission to the app, you should be able to find the Email information in the DynamoDB table.


## Next step

* Support more OpenID services providers.
* API for associating user email and SNS accounts.
* API for removing SNS account from user email.
