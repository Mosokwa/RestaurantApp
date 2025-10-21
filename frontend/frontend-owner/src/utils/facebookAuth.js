import { Facebook } from 'facebook-js-sdk';

let isFacebookSDKInitialized = false;

export const initFacebookSDK = () => {
  if (isFacebookSDKInitialized) return;

  return new Promise((resolve) => {
    window.fbAsyncInit = function() {
      window.FB.init({
        appId: import.meta.env.VITE_FACEBOOK_APP_ID,
        cookie: true,
        xfbml: true,
        version: 'v17.0'
      });
      
      isFacebookSDKInitialized = true;
      resolve();
    };

    // Load the Facebook SDK asynchronously
    (function(d, s, id) {
      var js, fjs = d.getElementsByTagName(s)[0];
      if (d.getElementById(id)) return;
      js = d.createElement(s); js.id = id;
      js.src = "https://connect.facebook.net/en_US/sdk.js";
      fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));
  });
};

export const loginWithFacebook = () => {
  return new Promise((resolve, reject) => {
    if (!isFacebookSDKInitialized) {
      reject(new Error('Facebook SDK not initialized'));
      return;
    }

    window.FB.login(function(response) {
      if (response.authResponse) {
        // User authorized the app
        const accessToken = response.authResponse.accessToken;
        
        // Get user profile information
        window.FB.api('/me', { fields: 'name,email' }, function(profileResponse) {
          if (profileResponse && !profileResponse.error) {
            resolve({
              accessToken: accessToken,
              userID: response.authResponse.userID,
              email: profileResponse.email,
              name: profileResponse.name
            });
          } else {
            reject(new Error('Failed to fetch Facebook profile'));
          }
        });
      } else {
        // User cancelled login or did not fully authorize
        reject(new Error('Facebook login cancelled or not authorized'));
      }
    }, { scope: 'email,public_profile' });
  });
};

// Utility to check if user is already logged in with Facebook
export const checkFacebookLoginStatus = () => {
  return new Promise((resolve) => {
    if (!isFacebookSDKInitialized) {
      resolve({ status: 'unknown' });
      return;
    }

    window.FB.getLoginStatus(function(response) {
      resolve(response);
    });
  });
};