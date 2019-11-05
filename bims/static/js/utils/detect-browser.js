// @ts-nocheck
'use strict';
// detect-browser.js v1.0.0
// Get Browser Data

// MIT License

// Copyright (c) 2018 Ahmad Raza

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.


function isMobile() {
	return /Mobi/.test(navigator.userAgent);
}

function getBrowserName() {
	// Opera 8.0+
	if ((window.opr && window.opr.addons)
		|| window.opera
		|| navigator.userAgent.indexOf(' OPR/') >= 0) {
		return 'Opera';
	}

	// Firefox 1.0+
	if (typeof InstallTrigger !== 'undefined') {
		return 'Firefox';
	}

	// Safari 3.0+ "[object HTMLElementConstructor]"
	if (/constructor/i.test(window.HTMLElement) || (function (p) {
		return p.toString() === '[object SafariRemoteNotification]';
	})(!window['safari'])) {
		return 'Safari';
	}

	// Internet Explorer 6-11
	if (/* @cc_on!@*/false || document.documentMode) {
		return 'Internet Explorer';
	}

	// Edge 20+
	if (!(document.documentMode) && window.StyleMedia) {
		return 'Microsoft Edge';
	}
	
	// Chrome
	if (window.chrome) {
		return 'Chrome';
	}
}

function getOSName() {
	let OSName = "Unknown";
	if (window.navigator.userAgent.indexOf("Windows NT 10.0") !== -1) OSName = "Windows 10";
	if (window.navigator.userAgent.indexOf("Windows NT 6.2") !== -1) OSName = "Windows 8";
	if (window.navigator.userAgent.indexOf("Windows NT 6.1") !== -1) OSName = "Windows 7";
	if (window.navigator.userAgent.indexOf("Windows NT 6.0") !== -1) OSName = "Windows Vista";
	if (window.navigator.userAgent.indexOf("Windows NT 5.1") !== -1) OSName = "Windows XP";
	if (window.navigator.userAgent.indexOf("Windows NT 5.0") !== -1) OSName = "Windows 2000";
	if (window.navigator.userAgent.indexOf("Mac") !== -1) OSName = "Mac/iOS";
	if (window.navigator.userAgent.indexOf("X11") !== -1) OSName = "UNIX";
	if (window.navigator.userAgent.indexOf("Linux") !== -1) OSName = "Linux";
	return OSName;
}

function getBrowser() {
	return {
		os: getOSName(),
		browser: getBrowserName(),
		language: navigator.language,
		languages: navigator.languages,
		user_agent: navigator.userAgent,
		device: isMobile() ? 'Mobile' : 'Desktop',
		referrer: document.referrer || 'N/A',
		online: navigator.onLine,
		timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
		screen_resolution: screen.width + ' x ' + screen.height,
		cookie_enabled: navigator.cookieEnabled,
	};
}


// var xhr = new XMLHttpRequest();
// xhr.open('GET', 'http://ip-api.com/json');
// xhr.onreadystatechange = function () {
// 	if (xhr.readyState == 4) {
// 		if (xhr.status == 200) {
// 			var IPdata = xhr.responseText;
// 			jsonResponse = JSON.parse(IPdata);
// 		}
// 	}
// };
// xhr.send(null);
