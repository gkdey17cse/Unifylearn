const express = require('express');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

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
        // Check if this is a follow-up query from a timestamp page
        const timestamp = req.query.timestamp;

        const response = await axios.post(`${BACKEND_URL}/query`, {
            query: req.body.query,
            timestamp: timestamp // Pass the timestamp to backend for context
        }, { timeout: 300000 });

        const results = response.data.results || [];
        const newTimestamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, 'Z');

        // Create folder for this timestamp
        const saveDir = path.resolve(__dirname, '../../Backend/results', newTimestamp);
        fs.mkdirSync(saveDir, { recursive: true });

        // Save results
        const polishedPath = path.join(saveDir, 'polished_results.json');
        fs.writeFileSync(polishedPath, JSON.stringify(results, null, 2));

        // Return results to frontend (no redirect)
        res.json({
            success: true,
            results,
            total_results: results.length,
            timestamp: newTimestamp
        });

    } catch (error) {
        console.error('Error calling backend:', error.message);
        res.status(500).json({
            success: false,
            error: error.message || 'Failed to process query'
        });
    }
});

// Timestamp route to render saved results
router.get('/:timestamp', (req, res) => {
    try {
        const polishedPath = path.resolve(
            __dirname,
            `../../Backend/results/${req.params.timestamp}/polished_results.json`
        );

        if (!fs.existsSync(polishedPath)) {
            // If file doesn't exist, redirect to home page instead of throwing error
            return res.redirect('/');
        }

        delete require.cache[require.resolve(polishedPath)];
        const raw = require(polishedPath);
        const courses = Array.isArray(raw) ? raw : (raw.results || raw);

        res.render('index', {
            title: `Course Search - ${req.params.timestamp}`,
            courses,
            loading: false,
            error: null,
            message: `Loaded ${courses.length} courses from polished_results.json`
        });

    } catch (err) {
        console.error('Error loading polished_results.json', err);
        // Redirect to home page instead of showing error
        res.redirect('/');
    }
});

module.exports = router;