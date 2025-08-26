const express = require('express');
const axios = require('axios');
const path = require('path');

const router = express.Router();
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000';

// Home page
router.get('/', (req, res) => {
    res.render('index', {
        title: 'Course Search',
        courses: [],
        loading: false,
        error: null,
        message: ''
    });
});

// Chatbot query
router.post('/query', async (req, res) => {
    try {
        const response = await axios.post(`${BACKEND_URL}/query`, {
            query: req.body.query
        }, { timeout: 300000 });

        // Ensure frontend-friendly structure
        res.json({
            success: true,
            results: response.data.results || [],
            total_results: response.data.results ? response.data.results.length : 0,
            timestamp: response.data.timestamp,
            saved_files: response.data.saved_files
        });

    } catch (error) {
        console.error('Error calling backend:', error.message);
        res.status(500).json({
            success: false,
            error: error.message || 'Failed to process query'
        });
    }
});

// Local testing with JSON
router.get('/test-local', (req, res) => {
    try {
        const polishedPath = path.resolve(
            __dirname,
            '../../Backend/results/20250825T190206Z/polished_results.json'
        );

        delete require.cache[require.resolve(polishedPath)];
        const raw = require(polishedPath);
        const courses = Array.isArray(raw) ? raw : (raw.results || raw);

        res.render('index', {
            title: 'Course Search - Local Test',
            courses: courses,
            loading: false,
            error: null,
            message: `Loaded ${courses.length} courses from polished_results.json`
        });
    } catch (err) {
        console.error('Error loading local polished_results.json', err);
        res.render('index', {
            title: 'Course Search - Local Test',
            courses: [],
            loading: false,
            error: 'Failed to load local JSON',
            message: ''
        });
    }
});

module.exports = router;
