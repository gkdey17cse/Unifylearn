// test-connectivity.js
const axios = require('axios');

async function testBackend() {
    const urls = [
        'http://127.0.0.1:5000/health',
        'http://localhost:5000/health'
    ];

    console.log('🧪 Testing backend connectivity...');

    for (const url of urls) {
        try {
            console.log(`\nTesting: ${url}`);
            const response = await axios.get(url, { timeout: 5000 });
            console.log('✅ SUCCESS:', response.status, response.data);
        } catch (error) {
            console.log('❌ FAILED:', error.code, error.message);
        }
    }
}

testBackend();