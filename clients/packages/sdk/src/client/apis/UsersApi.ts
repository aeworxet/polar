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
  HTTPValidationError,
  LoginResponse,
  LogoutResponse,
  UserRead,
  UserStripePortalSession,
  UserUpdateSettings,
} from '../models/index';

export interface UsersApiUpdatePreferencesRequest {
    userUpdateSettings: UserUpdateSettings;
}

/**
 * 
 */
export class UsersApi extends runtime.BaseAPI {

    /**
     * Create Stripe Customer Portal
     */
    async createStripeCustomerPortalRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<UserStripePortalSession>> {
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
            path: `/api/v1/users/me/stripe_customer_portal`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Create Stripe Customer Portal
     */
    async createStripeCustomerPortal(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<UserStripePortalSession> {
        const response = await this.createStripeCustomerPortalRaw(initOverrides);
        return await response.value();
    }

    /**
     * Create Token
     */
    async createTokenRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<LoginResponse>> {
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
            path: `/api/v1/users/me/token`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Create Token
     */
    async createToken(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<LoginResponse> {
        const response = await this.createTokenRaw(initOverrides);
        return await response.value();
    }

    /**
     * Get Authenticated
     */
    async getAuthenticatedRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<UserRead>> {
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
            path: `/api/v1/users/me`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Get Authenticated
     */
    async getAuthenticated(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<UserRead> {
        const response = await this.getAuthenticatedRaw(initOverrides);
        return await response.value();
    }

    /**
     * Logout
     */
    async logoutRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<LogoutResponse>> {
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
            path: `/api/v1/users/logout`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Logout
     */
    async logout(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<LogoutResponse> {
        const response = await this.logoutRaw(initOverrides);
        return await response.value();
    }

    /**
     * Update Preferences
     */
    async updatePreferencesRaw(requestParameters: UsersApiUpdatePreferencesRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<UserRead>> {
        if (requestParameters.userUpdateSettings === null || requestParameters.userUpdateSettings === undefined) {
            throw new runtime.RequiredError('userUpdateSettings','Required parameter requestParameters.userUpdateSettings was null or undefined when calling updatePreferences.');
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
            path: `/api/v1/users/me`,
            method: 'PUT',
            headers: headerParameters,
            query: queryParameters,
            body: requestParameters.userUpdateSettings,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Update Preferences
     */
    async updatePreferences(requestParameters: UsersApiUpdatePreferencesRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<UserRead> {
        const response = await this.updatePreferencesRaw(requestParameters, initOverrides);
        return await response.value();
    }

}
