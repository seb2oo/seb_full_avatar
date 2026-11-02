() => {
    console.log('🔥 AVATAR JS FILE EXECUTED');

    if (window.__avatarSyncCleanup) {
        window.__avatarSyncCleanup();
    }

    // ========================================================
    // CONFIGURATION
    // ========================================================

    const CHAT_ID = 'avatar-chatbot';
    const VIDEO_ID = 'avatar-video';
    const SIGNAL_ID = 'avatar-sync-signal';

    const OVERLAY_CLASS = 'avatar-sync-overlay';
    const NATIVE_CLASS = 'avatar-sync-native-hidden';
    const STYLE_ID = 'avatar-sync-style';

    // ========================================================
    // STATE
    // ========================================================

    let lastProcessedVideo = null;
    let phase = 'idle';

    let activeVideo = null;
    let fullText = '';
    let audioDuration = 0;

    let currentMessage = null;
    let currentNative = null;
    let currentOverlay = null;

    let scheduled = false;
    let disposed = false;

    // ========================================================
    // CSS
    // ========================================================

    if (!document.getElementById(STYLE_ID)) {

        const style = document.createElement('style');

        style.id = STYLE_ID;

        style.textContent = `
            #${CHAT_ID} .${NATIVE_CLASS} {
                display: none !important;
            }

            #${CHAT_ID} .${OVERLAY_CLASS} {
                white-space: pre-wrap;
                overflow-wrap: anywhere;
                font: inherit;
                line-height: inherit;
            }

            #${CHAT_ID}.avatar-sync-armed .message.bot:last-child,
            #${CHAT_ID}.avatar-sync-armed [data-testid="bot"]:last-child,
            #${CHAT_ID}.avatar-sync-armed .message-row.bot:last-child {
                visibility: hidden !important;
            }
        `;

        document.head.appendChild(style);
    }

    // ========================================================
    // DOM HELPERS
    // ========================================================

    function getChatbot() {
        return document.getElementById(CHAT_ID);
    }

    function getPhase() {

        const el = document.querySelector(
            `#${SIGNAL_ID} [data-avatar-phase]`
        );

        return el?.dataset.avatarPhase || 'idle';
    }


    function getLastAssistantMessage() {

        const chatbot = getChatbot();

        if (!chatbot) {
            return null;
        }

        // Retrieve messages in conversation order
        const messages = chatbot.querySelectorAll(
            '.message.user, .message.bot, [data-testid="user"], [data-testid="bot"]'
        );

        if (!messages.length) {
            return null;
        }

        const lastMessage = messages[messages.length - 1];

        // The last message belongs to the user:
        // the new assistant response does not exist yet.
        if (
            lastMessage.matches(
                '.message.user, [data-testid="user"]'
            )
        ) {
            return null;
        }

        // Only accept an assistant message
        if (
            lastMessage.matches(
                '.message.bot, [data-testid="bot"]'
            )
        ) {
            return lastMessage;
        }

        return null;
    }

    function getNativeContent(message) {

        if (!message) {
            return null;
        }

        const selectors = [
            '.message-body',
            '.message-content',
            '.prose',
            '.markdown'
        ];

        for (const selector of selectors) {

            const el = message.querySelector(selector);

            if (
                el &&
                !el.classList.contains(OVERLAY_CLASS)
            ) {
                return el;
            }
        }

        return null;
    }

    // ========================================================
    // OVERLAY MANAGEMENT
    // ========================================================

    function clearOverlay() {

        if (currentNative) {
            currentNative.classList.remove(NATIVE_CLASS);
        }

        if (currentOverlay) {
            currentOverlay.remove();
        }

        currentNative = null;
        currentOverlay = null;
        currentMessage = null;
    }


    function reset() {

        // Do not remove the previous message overlay.
        // Previous assistant messages must remain untouched.

        getChatbot()?.classList.remove('avatar-sync-armed');

        activeVideo = null;
        fullText = '';
        audioDuration = 0;

        // Forget references, but preserve the previous DOM.
        currentMessage = null;
        currentNative = null;
        currentOverlay = null;
    }


    function attachOverlay() {

        const message = getLastAssistantMessage();

        if (!message) {
            return false;
        }

        const native = getNativeContent(message);

        if (!native) {
            console.warn(
                '⚠️ Assistant Markdown container not found'
            );

            return false;
        }

        if (
            message !== currentMessage ||
            native !== currentNative ||
            !currentOverlay ||
            !currentOverlay.isConnected
        ) {

            clearOverlay();

            currentMessage = message;
            currentNative = native;

            currentOverlay = document.createElement('div');

            currentOverlay.className = OVERLAY_CLASS;

            currentOverlay.setAttribute(
                'aria-live',
                'off'
            );

            // Insert an independent element next to
            // the native Gradio Markdown content.
            //
            // Never replace Svelte-managed innerText.

            native.insertAdjacentElement(
                'afterend',
                currentOverlay
            );

            native.classList.add(NATIVE_CLASS);
        }

        return true;
    }


    function detectVideo() {

        if (phase !== 'ready') {
            return;
        }

        const video = document.getElementById(VIDEO_ID);

        if (!video) {
            return;
        }

        // Never reuse a video from a previous response.
        if (
            video === lastProcessedVideo &&
            video !== activeVideo
        ) {
            return;
        }

        const container =
            video.closest('#avatar-container') ||
            document.getElementById('avatar-container');

        if (!container) {
            return;
        }

        if (video !== activeVideo) {

            activeVideo = video;
            lastProcessedVideo = video;

            // ok this should have force an mobile phone to start move automatically but is not working... (start)
            video.playsInline = true;
            video.setAttribute('playsinline', '');
            video.setAttribute('webkit-playsinline', '');

            video.play().catch(error => {
                console.warn('Autoplay blocked:', error);
            });
            // end

            fullText = container.dataset.responseText || '';

            audioDuration = Number.parseFloat(
                video.dataset.audioDuration ||
                container.dataset.audioDuration ||
                '0'
            ) || 0;

            console.log('🎬 NEW VIDEO DETECTED', {
                text: fullText,
                duration: audioDuration
            });
        }

        if (!fullText) {
            return;
        }

        if (attachOverlay()) {

            renderText();

            getChatbot()?.classList.remove(
                'avatar-sync-armed'
            );
        }
    }

    // ========================================================
    // TEXT SYNCHRONIZATION
    // ========================================================

    function renderText() {

        if (
            !activeVideo ||
            !fullText ||
            phase !== 'ready'
        ) {
            return;
        }

        if (!attachOverlay()) {
            return;
        }

        const duration =
            Number.isFinite(activeVideo.duration) &&
            activeVideo.duration > 0
                ? activeVideo.duration
                : audioDuration;

        if (duration <= 0) {
            return;
        }

        const progress = Math.max(
            0,
            Math.min(
                activeVideo.currentTime / duration,
                1
            )
        );

        const length = activeVideo.ended
            ? fullText.length
            : Math.floor(fullText.length * progress);

        const next = fullText.slice(0, length);

        // Only modify our own independent element.
        // Never touch Gradio's Markdown nodes.

        if (currentOverlay.textContent !== next) {
            currentOverlay.textContent = next;
        }
    }

    // ========================================================
    // PHASE MANAGEMENT
    // ========================================================

    function updatePhase() {

        const next = getPhase();

        if (next === phase) {
            return;
        }

        console.log(
            `🎬 Avatar phase: ${phase} -> ${next}`
        );

        phase = next;

        if (
            phase === 'idle' ||
            phase === 'generating'
        ) {

            reset();

        } else if (phase === 'arming') {

            // Keep statuses visible during generation.
            // Prepare to hide the final assistant message.

            getChatbot()?.classList.add(
                'avatar-sync-armed'
            );

        } else if (phase === 'ready') {

            detectVideo();
        }
    }

    // ========================================================
    // VIDEO EVENTS
    // ========================================================

    function onVideoEvent(event) {

        if (event.target?.id !== VIDEO_ID) {
            return;
        }

        if (phase !== 'ready') {
            return;
        }

        detectVideo();

        if (event.type === 'play') {
            console.log('▶️ Avatar playback');
        }

        if (event.type === 'ended') {
            console.log('✅ Avatar playback ended');
        }

        renderText();
    }

    const events = [
        'play',
        'timeupdate',
        'seeking',
        'seeked',
        'ended',
        'loadedmetadata'
    ];

    for (const type of events) {

        document.addEventListener(
            type,
            onVideoEvent,
            true
        );
    }

    // ========================================================
    // MUTATION OBSERVER
    // ========================================================

    const observer = new MutationObserver(() => {

        if (scheduled || disposed) {
            return;
        }

        scheduled = true;

        requestAnimationFrame(() => {

            scheduled = false;

            if (disposed) {
                return;
            }


            updatePhase();

            if (phase === 'ready') {
                detectVideo();
            }
        });
    });

    observer.observe(
        document.body,
        {
            childList: true,
            subtree: true
        }
    );

    // ========================================================
    // INITIALIZATION
    // ========================================================

    updatePhase();
    detectVideo();

    // ========================================================
    // CLEANUP
    // ========================================================

    window.__avatarSyncCleanup = () => {

        disposed = true;

        observer.disconnect();

        for (const type of events) {

            document.removeEventListener(
                type,
                onVideoEvent,
                true
            );
        }

        reset();
    };

    console.log('✅ Avatar synchronization ready');
}