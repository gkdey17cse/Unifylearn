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
        const response = await axios.post(`${BACKEND_URL}/query`, {
            query: req.body.query
        }, { timeout: 300000 });

        const results = response.data.results || [];
        const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, 'Z');

        // Create folder for this timestamp
        const saveDir = path.resolve(__dirname, '../../Backend/results', timestamp);
        fs.mkdirSync(saveDir, { recursive: true });

        // Save results
        const polishedPath = path.join(saveDir, 'polished_results.json');
        fs.writeFileSync(polishedPath, JSON.stringify(results, null, 2));

        // Return timestamp to frontend
        res.json({
            success: true,
            results,
            total_results: results.length,
            timestamp
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

        if (!fs.existsSync(polishedPath)) throw new Error('File not found');

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
        res.render('index', {
            title: 'Course Search',
            courses: [],
            loading: false,
            error: 'Failed to load JSON',
            message: ''
        });
    }
});

// Local testing with JSON (optional) CURRENTLY DISABLE
// router.get('/test-local', (req, res) => {
//     try {
//         const polishedPath = path.resolve(
//             __dirname,
//             '../../Backend/results/20250825T190206Z/polished_results.json'
//         );

//         delete require.cache[require.resolve(polishedPath)];
//         const raw = require(polishedPath);
//         const courses = Array.isArray(raw) ? raw : (raw.results || raw);

//         res.render('index', {
//             title: 'Course Search - Local Test',
//             courses,
//             loading: false,
//             error: null,
//             message: `Loaded ${courses.length} courses from polished_results.json`
//         });

//     } catch (err) {
//         console.error('Error loading local polished_results.json', err);
//         res.render('index', {
//             title: 'Course Search - Local Test',
//             courses: [],
//             loading: false,
//             error: 'Failed to load local JSON',
//             message: ''
//         });
//     }
// });

module.exports = router;
