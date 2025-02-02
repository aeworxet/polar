/* tslint:disable */
/* eslint-disable */
/**
 * Polar API
 *  Welcome to the **Polar API** for [polar.sh](https://polar.sh).  The Public API is currently a [work in progress](https://github.com/polarsource/polar/issues/834) and is in active development. 🚀  #### Authentication  Use a [Personal Access Token](https://polar.sh/settings) and send it in the `Authorization` header on the format `Bearer [YOUR_TOKEN]`.  #### Feedback  If you have any feedback or comments, reach out in the [Polar API-issue](https://github.com/polarsource/polar/issues/834), or reach out on the Polar Discord server.  We\'d love to see what you\'ve built with the API and to get your thoughts on how we can make the API better!  #### Connecting  The Polar API is online at `https://api.polar.sh`. 
 *
 * The version of the OpenAPI document: 0.1.0
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */


import * as runtime from '../runtime';
import type {
  AuthorizationResponse,
  GithubBadgeRead,
  GithubUser,
  HTTPValidationError,
  InstallationCreate,
  LoginResponse,
  LookupUserRequest,
  OrganizationPrivateRead,
  PolarIntegrationsGithubEndpointsWebhookResponse,
  PolarIntegrationsStripeEndpointsWebhookResponse,
  UserSignupType,
} from '../models/index';

export interface IntegrationsApiGetBadgeSettingsRequest {
    org: string;
    repo: string;
    number: number;
    badgeType: GetBadgeSettingsBadgeTypeEnum;
}

export interface IntegrationsApiGithubAuthorizeRequest {
    paymentIntentId?: string;
    gotoUrl?: string;
    userSignupType?: UserSignupType;
}

export interface IntegrationsApiGithubCallbackRequest {
    code?: string;
    codeVerifier?: string;
    state?: string;
    error?: string;
}

export interface IntegrationsApiInstallRequest {
    installationCreate: InstallationCreate;
}

export interface IntegrationsApiLookupUserOperationRequest {
    lookupUserRequest: LookupUserRequest;
}

export interface IntegrationsApiStripeConnectReturnRequest {
    stripeId: string;
}

/**
 * 
 */
export class IntegrationsApi extends runtime.BaseAPI {

    /**
     * Get Badge Settings
     */
    async getBadgeSettingsRaw(requestParameters: IntegrationsApiGetBadgeSettingsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<GithubBadgeRead>> {
        if (requestParameters.org === null || requestParameters.org === undefined) {
            throw new runtime.RequiredError('org','Required parameter requestParameters.org was null or undefined when calling getBadgeSettings.');
        }

        if (requestParameters.repo === null || requestParameters.repo === undefined) {
            throw new runtime.RequiredError('repo','Required parameter requestParameters.repo was null or undefined when calling getBadgeSettings.');
        }

        if (requestParameters.number === null || requestParameters.number === undefined) {
            throw new runtime.RequiredError('number','Required parameter requestParameters.number was null or undefined when calling getBadgeSettings.');
        }

        if (requestParameters.badgeType === null || requestParameters.badgeType === undefined) {
            throw new runtime.RequiredError('badgeType','Required parameter requestParameters.badgeType was null or undefined when calling getBadgeSettings.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/github/{org}/{repo}/issues/{number}/badges/{badge_type}`.replace(`{${"org"}}`, encodeURIComponent(String(requestParameters.org))).replace(`{${"repo"}}`, encodeURIComponent(String(requestParameters.repo))).replace(`{${"number"}}`, encodeURIComponent(String(requestParameters.number))).replace(`{${"badge_type"}}`, encodeURIComponent(String(requestParameters.badgeType))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Get Badge Settings
     */
    async getBadgeSettings(requestParameters: IntegrationsApiGetBadgeSettingsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<GithubBadgeRead> {
        const response = await this.getBadgeSettingsRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Github Authorize
     */
    async githubAuthorizeRaw(requestParameters: IntegrationsApiGithubAuthorizeRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<AuthorizationResponse>> {
        const queryParameters: any = {};

        if (requestParameters.paymentIntentId !== undefined) {
            queryParameters['payment_intent_id'] = requestParameters.paymentIntentId;
        }

        if (requestParameters.gotoUrl !== undefined) {
            queryParameters['goto_url'] = requestParameters.gotoUrl;
        }

        if (requestParameters.userSignupType !== undefined) {
            queryParameters['user_signup_type'] = requestParameters.userSignupType;
        }

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/github/authorize`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Github Authorize
     */
    async githubAuthorize(requestParameters: IntegrationsApiGithubAuthorizeRequest = {}, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<AuthorizationResponse> {
        const response = await this.githubAuthorizeRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Github Callback
     */
    async githubCallbackRaw(requestParameters: IntegrationsApiGithubCallbackRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<LoginResponse>> {
        const queryParameters: any = {};

        if (requestParameters.code !== undefined) {
            queryParameters['code'] = requestParameters.code;
        }

        if (requestParameters.codeVerifier !== undefined) {
            queryParameters['code_verifier'] = requestParameters.codeVerifier;
        }

        if (requestParameters.state !== undefined) {
            queryParameters['state'] = requestParameters.state;
        }

        if (requestParameters.error !== undefined) {
            queryParameters['error'] = requestParameters.error;
        }

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/github/callback`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Github Callback
     */
    async githubCallback(requestParameters: IntegrationsApiGithubCallbackRequest = {}, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<LoginResponse> {
        const response = await this.githubCallbackRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Install
     */
    async installRaw(requestParameters: IntegrationsApiInstallRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<OrganizationPrivateRead>> {
        if (requestParameters.installationCreate === null || requestParameters.installationCreate === undefined) {
            throw new runtime.RequiredError('installationCreate','Required parameter requestParameters.installationCreate was null or undefined when calling install.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/github/installations`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: requestParameters.installationCreate,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Install
     */
    async install(requestParameters: IntegrationsApiInstallRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<OrganizationPrivateRead> {
        const response = await this.installRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Lookup User
     */
    async lookupUserRaw(requestParameters: IntegrationsApiLookupUserOperationRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<GithubUser>> {
        if (requestParameters.lookupUserRequest === null || requestParameters.lookupUserRequest === undefined) {
            throw new runtime.RequiredError('lookupUserRequest','Required parameter requestParameters.lookupUserRequest was null or undefined when calling lookupUser.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/github/lookup_user`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: requestParameters.lookupUserRequest,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Lookup User
     */
    async lookupUser(requestParameters: IntegrationsApiLookupUserOperationRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<GithubUser> {
        const response = await this.lookupUserRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Stripe Connect Refresh
     */
    async stripeConnectRefreshRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<PolarIntegrationsStripeEndpointsWebhookResponse>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/stripe/refresh`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Stripe Connect Refresh
     */
    async stripeConnectRefresh(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<PolarIntegrationsStripeEndpointsWebhookResponse> {
        const response = await this.stripeConnectRefreshRaw(initOverrides);
        return await response.value();
    }

    /**
     * Stripe Connect Return
     */
    async stripeConnectReturnRaw(requestParameters: IntegrationsApiStripeConnectReturnRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<any>> {
        if (requestParameters.stripeId === null || requestParameters.stripeId === undefined) {
            throw new runtime.RequiredError('stripeId','Required parameter requestParameters.stripeId was null or undefined when calling stripeConnectReturn.');
        }

        const queryParameters: any = {};

        if (requestParameters.stripeId !== undefined) {
            queryParameters['stripe_id'] = requestParameters.stripeId;
        }

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/stripe/return`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Stripe Connect Return
     */
    async stripeConnectReturn(requestParameters: IntegrationsApiStripeConnectReturnRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<any> {
        const response = await this.stripeConnectReturnRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Webhook
     */
    async webhookRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<PolarIntegrationsGithubEndpointsWebhookResponse>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/github/webhook`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Webhook
     */
    async webhook(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<PolarIntegrationsGithubEndpointsWebhookResponse> {
        const response = await this.webhookRaw(initOverrides);
        return await response.value();
    }

    /**
     * Webhook
     */
    async webhook_1Raw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<PolarIntegrationsStripeEndpointsWebhookResponse>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/integrations/stripe/webhook`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Webhook
     */
    async webhook_1(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<PolarIntegrationsStripeEndpointsWebhookResponse> {
        const response = await this.webhook_1Raw(initOverrides);
        return await response.value();
    }

}

/**
 * @export
 */
export const GetBadgeSettingsBadgeTypeEnum = {
    PLEDGE: 'pledge'
} as const;
export type GetBadgeSettingsBadgeTypeEnum = typeof GetBadgeSettingsBadgeTypeEnum[keyof typeof GetBadgeSettingsBadgeTypeEnum];
