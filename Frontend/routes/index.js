const express = require('express');
const axios = require('axios');

const router = express.Router();
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000';

// Home page
router.get('/', (req, res) => {
    res.render('index', {
        title: 'Course Search',
        courses: [],
        loading: false,
        error: null
    });
});

// Handle query submission
router.post('/query', async (req, res) => {
    try {
        console.log('Sending query to backend:', req.body.query);
        console.log('Backend URL:', `${BACKEND_URL}/query`);

        // Test connection first
        try {
            await axios.get(`${BACKEND_URL}/health`, { timeout: 5000 });
        } catch (healthError) {
            console.error('Backend health check failed:', healthError.message);
            return res.status(503).json({
                success: false,
                error: 'Backend service is unavailable. Please make sure the backend server is running on port 5000.'
            });
        }

        const response = await axios.post(`${BACKEND_URL}/query`, {
            query: req.body.query
        }, {
            timeout: 300000 // 5 minute timeout for long-running queries
        });

        console.log('Backend response received');

        // Check if backend response already has success field
        if (response.data.success !== undefined) {
            // Backend already structured the response properly
            res.json(response.data);
        } else {
            // Structure the response for frontend compatibility
            res.json({
                success: true,
                results: response.data.results || [],
                total_results: response.data.results ? response.data.results.length : 0,
                timestamp: response.data.timestamp,
                saved_files: response.data.saved_files
            });
        }
    } catch (error) {
        console.error('Error calling backend:', error.message);

        if (error.code === 'ECONNREFUSED') {
            res.status(503).json({
                success: false,
                error: 'Cannot connect to backend server. Please make sure it is running on port 5000.'
            });
        } else if (error.response) {
            res.status(error.response.status).json({
                success: false,
                error: error.response.data.error || 'Backend returned an error'
            });
        } else if (error.code === 'ECONNABORTED') {
            res.status(504).json({
                success: false,
                error: 'Request timeout. The query is taking too long to process.'
            });
        } else {
            res.status(500).json({
                success: false,
                error: 'Failed to process query: ' + error.message
            });
        }
    }
});

// Get saved results
router.get('/results/:timestamp', async (req, res) => {
    try {
        const response = await axios.get(`${BACKEND_URL}/results/${req.params.timestamp}`);
        res.json(response.data);
    } catch (error) {
        console.error('Error fetching results:', error.message);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch results'
        });
    }
});

// Test backend connection
router.get('/test-backend', async (req, res) => {
    try {
        const response = await axios.get(`${BACKEND_URL}/health`);
        res.json({
            success: true,
            message: 'Backend is reachable',
            backendResponse: response.data
        });
    } catch (error) {
        res.json({
            success: false,
            message: 'Backend is not reachable',
            error: error.message
        });
    }
});

module.exports = router;