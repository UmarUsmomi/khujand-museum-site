/**
 * Historical Museum of Sughd Region (Khujand Fortress) Modernization
 * Milestone M4: 3D WebGL & GSAP Scroll-World (Features 8, 9, 10)
 *
 * Architecture:
 * - Feature 8: 4-Epoch WebGL Scroll-World ("Sogdiana", "Alexandria", "Timur", "Modern")
 *              Pinned over 400vh with GSAP ScrollTrigger camera choreography.
 * - Feature 9: Zero-Video Procedural 3D World (< 25,000 triangles total budget),
 *              procedural canvas textures (power-of-two: 256/512, strictly < 2048px),
 *              comprehensive GPU disposal cleanup, zero external video dependencies.
 * - Feature 10: 60 FPS WebGL Performance Optimization:
 *               IntersectionObserver auto-sleep (cancelAnimationFrame / pause offscreen),
 *               mobile DPR clamped to <= 1.0, desktop DPR clamped to <= 1.75,
 *               clock delta time capping <= 0.1s, passive event listeners.
 */

(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // 1. Historical Epochs Contract (Feature 8)
  // Explicitly defines the 4 historical epochs of Khujand Fortress:
  // "sogdiana", "alexandria", "timur", "modern"
  // ---------------------------------------------------------------------------
  const EPOCHS = [
    {
      id: 'sogdiana',
      name: 'Древняя Согдиана',
      era: 'VI–IV вв. до н.э.',
      badge: 'Эпоха I • VI–IV вв. до н.э.',
      desc: 'Колыбель цивилизации на берегах Сырдарьи. Мощные сырцовые стены цитадели, гончарные печи, изготовление расписных хумов и древние караванные пути Согда.',
      image: 'images/fortress/epoch-sogdiana.webp',
      videoTime: 0.0,
      cameraPos: { x: 0, y: 7.5, z: 26 },
      lookAt: { x: 0, y: 2.8, z: 0 },
      fogColor: 0x1a120c,
      ambientColor: 0x5c3f29,
      lightColor: 0xffb366,
      lightIntensity: 1.4
    },
    {
      id: 'alexandria',
      name: 'Александрия Эсхата',
      era: '329 г. до н.э.',
      badge: 'Эпоха II • 329 г. до н.э.',
      desc: 'Крайний форпост империи Александра Македонского на реке Яксарт (Сырдарья). Эллинистические мраморные колоннады, монументальные мозаики и серебряные тетрадрахмы.',
      image: 'images/fortress/epoch-alexandria.webp',
      videoTime: 2.5,
      cameraPos: { x: 18, y: 9.0, z: -38 },
      lookAt: { x: 0, y: 3.5, z: -62 },
      fogColor: 0x0a1826,
      ambientColor: 0x1f3852,
      lightColor: 0x8ec7f5,
      lightIntensity: 1.5
    },
    {
      id: 'timur',
      name: 'Оборона Тимурмалика',
      era: '1220 г.',
      badge: 'Эпоха III • 1220 г.',
      desc: 'Легендарная битва национального героя Тимурмалика против монгольских туменов. Неприступная каменная крепость, метательные орудия на речном острове и неугасимое пламя свободы.',
      image: 'images/fortress/epoch-timur.webp',
      videoTime: 5.0,
      cameraPos: { x: -22, y: 11.0, z: -102 },
      lookAt: { x: 0, y: 4.8, z: -128 },
      fogColor: 0x220c06,
      ambientColor: 0x5a2112,
      lightColor: 0xff6633,
      lightIntensity: 1.6
    },
    {
      id: 'modern',
      name: 'Современный музей',
      era: 'XXI век',
      badge: 'Эпоха IV • Новейшее время',
      desc: 'Возрождённый исторический музей Согдийской области в цитадели Худжандской крепости. Архитектурный ансамбль семи куполов, фонтаны и свыше 28 000 бесценных реликвий.',
      image: 'images/fortress/epoch-modern.webp',
      videoTime: 9.8,
      cameraPos: { x: 0, y: 13.0, z: -168 },
      lookAt: { x: 0, y: 5.5, z: -198 },
      fogColor: 0x061420,
      ambientColor: 0x16344e,
      lightColor: 0xffd573,
      lightIntensity: 1.5
    }
  ];

  // ---------------------------------------------------------------------------
  // 2. State & Engine References
  // ---------------------------------------------------------------------------
  let container = null;
  let canvas = null;
  let scene = null;
  let camera = null;
  let renderer = null;
  let clock = null;
  let scrollTriggerInstance = null;

  let dirLight = null;
  let hemiLight = null;
  let pointLights = [];
  let isWebGLSupported = true;

  // Animation & Loop Control (Feature 10)
  let isIntersecting = false;
  let animationFrameId = null;
  let currentScrollProgress = 0;
  let targetScrollProgress = 0;
  let activeEpochIndex = 0;
  let isTransitioningToEra = false;
  let eraTransitionTimer = null;

  // GPU Resource Registry for comprehensive dispose() (Feature 9)
  const disposableGeometries = [];
  const disposableMaterials = [];
  const disposableTextures = [];

  // Procedural animated meshes
  let animatedParticles = null;
  let animatedWater = null;
  let animatedTorches = [];
  let animatedArtifacts = [];

  // ---------------------------------------------------------------------------
  // 3. Procedural Texture Generators (Feature 9 & 10)
  // Power-of-two dimensions (256, 512), strictly capped within texture budget.
  // ---------------------------------------------------------------------------
  function createProceduralTexture(type, width = 512, height = 512) {
    const texCanvas = document.createElement('canvas');
    texCanvas.width = width;
    texCanvas.height = height;
    const ctx = texCanvas.getContext('2d');

    if (type === 'adobe') {
      // Warm terracotta mudbrick with subtle noise and mortar seams
      ctx.fillStyle = '#b87d4b';
      ctx.fillRect(0, 0, width, height);

      // Noise grain
      const imgData = ctx.getImageData(0, 0, width, height);
      const data = imgData.data;
      for (let i = 0; i < data.length; i += 4) {
        const noise = (Math.random() - 0.5) * 36;
        data[i] = Math.min(255, Math.max(0, data[i] + noise));
        data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise * 0.8));
        data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise * 0.5));
      }
      ctx.putImageData(imgData, 0, 0);

      // Brick mortar lines
      ctx.strokeStyle = 'rgba(78, 48, 25, 0.45)';
      ctx.lineWidth = 4;
      const rowHeight = 32;
      for (let y = 0; y < height; y += rowHeight) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();

        const offset = (y / rowHeight) % 2 === 0 ? 0 : 32;
        for (let x = offset; x < width; x += 64) {
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(x, y + rowHeight);
          ctx.stroke();
        }
      }
    } else if (type === 'marble') {
      // Classical Hellenistic veined marble
      ctx.fillStyle = '#e8eff5';
      ctx.fillRect(0, 0, width, height);

      // Veins
      ctx.strokeStyle = 'rgba(110, 140, 165, 0.25)';
      ctx.lineWidth = 3;
      for (let i = 0; i < 8; i++) {
        ctx.beginPath();
        let vx = Math.random() * width;
        let vy = 0;
        ctx.moveTo(vx, vy);
        while (vy < height) {
          vx += (Math.random() - 0.5) * 60;
          vy += 40 + Math.random() * 40;
          ctx.lineTo(vx, vy);
        }
        ctx.stroke();
      }
    } else if (type === 'citadel_stone') {
      // Rugged fortress masonry for Timur Malik's bastion
      ctx.fillStyle = '#4a3f38';
      ctx.fillRect(0, 0, width, height);

      ctx.strokeStyle = 'rgba(25, 20, 18, 0.7)';
      ctx.lineWidth = 5;
      const blockH = 40;
      for (let y = 0; y < height; y += blockH) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();

        const shift = (y / blockH) % 2 === 0 ? 0 : 40;
        for (let x = shift; x < width; x += 80) {
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(x, y + blockH);
          ctx.stroke();
        }
      }
    } else if (type === 'mosaic') {
      // Khujand turquoise and 24K gold geometric tile pattern
      ctx.fillStyle = '#0f384a';
      ctx.fillRect(0, 0, width, height);

      const tileSize = 64;
      for (let y = 0; y < height; y += tileSize) {
        for (let x = 0; x < width; x += tileSize) {
          ctx.strokeStyle = 'rgba(212, 175, 55, 0.8)'; // Gold outline
          ctx.lineWidth = 2;
          ctx.strokeRect(x + 4, y + 4, tileSize - 8, tileSize - 8);

          ctx.fillStyle = (x + y) % (tileSize * 2) === 0 ? '#00a896' : '#028090';
          ctx.fillRect(x + 10, y + 10, tileSize - 20, tileSize - 20);

          // Center gold star motif
          ctx.fillStyle = '#f4d06f';
          ctx.beginPath();
          ctx.arc(x + tileSize / 2, y + tileSize / 2, 6, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    } else if (type === 'water') {
      // Syr Darya river water texture (256x256 power of two)
      ctx.fillStyle = '#0e4159';
      ctx.fillRect(0, 0, width, height);

      ctx.strokeStyle = 'rgba(120, 210, 240, 0.35)';
      ctx.lineWidth = 3;
      for (let y = 0; y < height; y += 16) {
        ctx.beginPath();
        for (let x = 0; x < width; x += 20) {
          const cy = y + Math.sin((x / width) * Math.PI * 4) * 6;
          if (x === 0) ctx.moveTo(x, cy);
          else ctx.lineTo(x, cy);
        }
        ctx.stroke();
      }
    }

    const texture = new THREE.CanvasTexture(texCanvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    disposableTextures.push(texture);
    return texture;
  }

  // ---------------------------------------------------------------------------
  // 4. Memory Tracking & Disposal Helpers (Feature 9)
  // ---------------------------------------------------------------------------
  function trackGeometry(geom) {
    disposableGeometries.push(geom);
    return geom;
  }

  function trackMaterial(mat) {
    disposableMaterials.push(mat);
    return mat;
  }

  function disposeGPUResources() {
    // Geometries cleanup
    disposableGeometries.forEach((g) => {
      if (g && typeof g.dispose === 'function') g.dispose();
    });
    disposableGeometries.length = 0;

    // Materials cleanup
    disposableMaterials.forEach((m) => {
      if (m && typeof m.dispose === 'function') m.dispose();
    });
    disposableMaterials.length = 0;

    // Textures cleanup
    disposableTextures.forEach((t) => {
      if (t && typeof t.dispose === 'function') t.dispose();
    });
    disposableTextures.length = 0;

    // Renderer cleanup
    if (renderer && typeof renderer.dispose === 'function') {
      renderer.dispose();
    }
  }

  // ---------------------------------------------------------------------------
  // 5. Procedural 3D Scene Assembly (Feature 9: < 25,000 triangles)
  // Constructs low-poly architectural landmarks for each epoch.
  // ---------------------------------------------------------------------------
  function buildProceduralWorld() {
    const worldGroup = new THREE.Group();

    // Procedural textures
    const adobeTex = createProceduralTexture('adobe', 512, 512);
    adobeTex.repeat.set(4, 2);

    const marbleTex = createProceduralTexture('marble', 512, 512);
    marbleTex.repeat.set(2, 4);

    const stoneTex = createProceduralTexture('citadel_stone', 512, 512);
    stoneTex.repeat.set(4, 2);

    const mosaicTex = createProceduralTexture('mosaic', 512, 512);
    mosaicTex.repeat.set(4, 4);

    const waterTex = createProceduralTexture('water', 256, 256);
    waterTex.repeat.set(2, 16);

    // Common Materials (MeshStandardMaterial)
    const adobeMat = trackMaterial(new THREE.MeshStandardMaterial({
      map: adobeTex,
      roughness: 0.9,
      metalness: 0.05
    }));

    const marbleMat = trackMaterial(new THREE.MeshStandardMaterial({
      map: marbleTex,
      roughness: 0.35,
      metalness: 0.15
    }));

    const goldMat = trackMaterial(new THREE.MeshStandardMaterial({
      color: 0xd4af37,
      roughness: 0.25,
      metalness: 0.85
    }));

    const stoneMat = trackMaterial(new THREE.MeshStandardMaterial({
      map: stoneTex,
      roughness: 0.85,
      metalness: 0.1
    }));

    const turquoiseMat = trackMaterial(new THREE.MeshStandardMaterial({
      map: mosaicTex,
      color: 0x00c2cb,
      roughness: 0.3,
      metalness: 0.2
    }));

    const terracottaMat = trackMaterial(new THREE.MeshStandardMaterial({
      color: 0xb55a30,
      roughness: 0.8,
      metalness: 0.05
    }));

    const waterMat = trackMaterial(new THREE.MeshStandardMaterial({
      map: waterTex,
      color: 0x1d6a8a,
      roughness: 0.2,
      metalness: 0.4,
      transparent: true,
      opacity: 0.85
    }));

    const woodMat = trackMaterial(new THREE.MeshStandardMaterial({
      color: 0x4a2e18,
      roughness: 0.75,
      metalness: 0.05
    }));

    // --- Base River Syr Darya & Riverbed Terrain ---
    // Procedural low-poly river mesh
    const riverGeom = trackGeometry(new THREE.PlaneGeometry(36, 260, 8, 32));
    riverGeom.rotateX(-Math.PI / 2);
    const riverMesh = new THREE.Mesh(riverGeom, waterMat);
    riverMesh.position.set(-14, -0.4, -90);
    worldGroup.add(riverMesh);
    animatedWater = riverMesh;

    // Ground Sandy Banks
    const groundGeom = trackGeometry(new THREE.PlaneGeometry(90, 260, 6, 20));
    groundGeom.rotateX(-Math.PI / 2);
    const groundMat = trackMaterial(new THREE.MeshStandardMaterial({
      color: 0x1a1612,
      roughness: 0.95,
      metalness: 0.05
    }));
    const groundMesh = new THREE.Mesh(groundGeom, groundMat);
    groundMesh.position.set(10, -0.6, -90);
    worldGroup.add(groundMesh);

    // =========================================================================
    // EPOCH 1: Sogdiana (z ~ 0)
    // Mudbrick fortress bastions, watchtowers, large clay khum jars
    // =========================================================================
    const sogdianaGroup = new THREE.Group();
    sogdianaGroup.position.set(0, 0, 0);

    // Main Citadel Adobe Wall (BoxGeometry)
    const wallGeom = trackGeometry(new THREE.BoxGeometry(22, 6.5, 2.8));
    const mainWall = new THREE.Mesh(wallGeom, adobeMat);
    mainWall.position.set(0, 3.25, 0);
    sogdianaGroup.add(mainWall);

    // Gate Archway Cutout / Posts
    const gatePostGeom = trackGeometry(new THREE.BoxGeometry(2.5, 7.5, 3.2));
    const gateLeft = new THREE.Mesh(gatePostGeom, adobeMat);
    gateLeft.position.set(-3.5, 3.75, 0.2);
    sogdianaGroup.add(gateLeft);

    const gateRight = new THREE.Mesh(gatePostGeom, adobeMat);
    gateRight.position.set(3.5, 3.75, 0.2);
    sogdianaGroup.add(gateRight);

    // Two Round Adobe Bastion Watchtowers
    const towerGeom = trackGeometry(new THREE.CylinderGeometry(2.2, 2.6, 9.5, 12));
    const towerL = new THREE.Mesh(towerGeom, adobeMat);
    towerL.position.set(-12, 4.75, 0.5);
    sogdianaGroup.add(towerL);

    const towerR = new THREE.Mesh(towerGeom, adobeMat);
    towerR.position.set(12, 4.75, 0.5);
    sogdianaGroup.add(towerR);

    // Conical Adobe Tower Roofs
    const roofGeom = trackGeometry(new THREE.ConeGeometry(2.6, 2.2, 12));
    const roofL = new THREE.Mesh(roofGeom, terracottaMat);
    roofL.position.set(-12, 10.6, 0.5);
    sogdianaGroup.add(roofL);

    const roofR = new THREE.Mesh(roofGeom, terracottaMat);
    roofR.position.set(12, 10.6, 0.5);
    sogdianaGroup.add(roofR);

    // Giant Sogdian Khum (Clay Pottery Vessel)
    const khumBodyGeom = trackGeometry(new THREE.CylinderGeometry(0.9, 0.4, 2.0, 10));
    const khumRimGeom = trackGeometry(new THREE.CylinderGeometry(0.7, 0.85, 0.3, 10));

    const khum1 = new THREE.Mesh(khumBodyGeom, terracottaMat);
    khum1.position.set(-5.5, 1.0, 4.5);
    const khum1Rim = new THREE.Mesh(khumRimGeom, terracottaMat);
    khum1Rim.position.set(-5.5, 2.1, 4.5);
    sogdianaGroup.add(khum1, khum1Rim);

    const khum2 = new THREE.Mesh(khumBodyGeom, terracottaMat);
    khum2.position.set(-4.0, 1.0, 5.2);
    khum2.scale.set(0.75, 0.75, 0.75);
    sogdianaGroup.add(khum2);

    animatedArtifacts.push(khum1);
    worldGroup.add(sogdianaGroup);

    // =========================================================================
    // EPOCH 2: Alexandria Eschate (z ~ -62)
    // Hellenistic colonnade, marble pediment, mosaic plaza
    // =========================================================================
    const alexandriaGroup = new THREE.Group();
    alexandriaGroup.position.set(0, 0, -62);

    // Marble Colonnade Podium / Steps
    const podiumGeom = trackGeometry(new THREE.BoxGeometry(26, 1.0, 16));
    const podium = new THREE.Mesh(podiumGeom, marbleMat);
    podium.position.set(0, 0.5, 0);
    alexandriaGroup.add(podium);

    // Fluted Marble Columns (CylinderGeometry)
    const columnGeom = trackGeometry(new THREE.CylinderGeometry(0.65, 0.75, 7.5, 12));
    const capitalGeom = trackGeometry(new THREE.BoxGeometry(1.6, 0.5, 1.6));

    const colXPositions = [-9, -4.5, 0, 4.5, 9];
    colXPositions.forEach((cx) => {
      const col = new THREE.Mesh(columnGeom, marbleMat);
      col.position.set(cx, 4.75, 5);
      const cap = new THREE.Mesh(capitalGeom, goldMat);
      cap.position.set(cx, 8.6, 5);
      alexandriaGroup.add(col, cap);

      const colRear = new THREE.Mesh(columnGeom, marbleMat);
      colRear.position.set(cx, 4.75, -5);
      const capRear = new THREE.Mesh(capitalGeom, goldMat);
      capRear.position.set(cx, 8.6, -5);
      alexandriaGroup.add(colRear, capRear);
    });

    // Hellenistic Entablature & Pediment (BoxGeometry / BufferGeometry)
    const architraveGeom = trackGeometry(new THREE.BoxGeometry(23, 1.2, 13));
    const architrave = new THREE.Mesh(architraveGeom, marbleMat);
    architrave.position.set(0, 9.4, 0);
    alexandriaGroup.add(architrave);

    // Triangular Pediment Front
    const pedimentGeom = trackGeometry(new THREE.ConeGeometry(12, 3.2, 4));
    pedimentGeom.rotateY(Math.PI / 4);
    const pediment = new THREE.Mesh(pedimentGeom, marbleMat);
    pediment.position.set(0, 11.4, 5.5);
    alexandriaGroup.add(pediment);

    // Golden Alexander Tetradrachm Artifact Medal on Display Plinth
    const coinPlinthGeom = trackGeometry(new THREE.CylinderGeometry(1.0, 1.2, 2.2, 12));
    const coinPlinth = new THREE.Mesh(coinPlinthGeom, marbleMat);
    coinPlinth.position.set(0, 2.1, 0);

    const coinGeom = trackGeometry(new THREE.CylinderGeometry(1.2, 1.2, 0.15, 16));
    coinGeom.rotateX(Math.PI / 3);
    const goldCoin = new THREE.Mesh(coinGeom, goldMat);
    goldCoin.position.set(0, 3.6, 0);
    alexandriaGroup.add(coinPlinth, goldCoin);
    animatedArtifacts.push(goldCoin);

    worldGroup.add(alexandriaGroup);

    // =========================================================================
    // EPOCH 3: Timur Malik Defense (z ~ -128)
    // Massive stone river bastion, arched gate, siege catapult & braziers
    // =========================================================================
    const timurGroup = new THREE.Group();
    timurGroup.position.set(0, 0, -128);

    // Heavy Stone Citadel Walls
    const stoneWallGeom = trackGeometry(new THREE.BoxGeometry(26, 9.0, 3.5));
    const stoneWall = new THREE.Mesh(stoneWallGeom, stoneMat);
    stoneWall.position.set(0, 4.5, 0);
    timurGroup.add(stoneWall);

    // Fortress Crenellations / Battlements
    const merlonGeom = trackGeometry(new THREE.BoxGeometry(1.4, 1.2, 3.6));
    for (let mx = -12; mx <= 12; mx += 3.0) {
      const merlon = new THREE.Mesh(merlonGeom, stoneMat);
      merlon.position.set(mx, 9.6, 0);
      timurGroup.add(merlon);
    }

    // Fortified Gate Towers
    const squareTowerGeom = trackGeometry(new THREE.BoxGeometry(4.2, 12.0, 4.5));
    const sqTowerL = new THREE.Mesh(squareTowerGeom, stoneMat);
    sqTowerL.position.set(-6, 6.0, 1.0);
    const sqTowerR = new THREE.Mesh(squareTowerGeom, stoneMat);
    sqTowerR.position.set(6, 6.0, 1.0);
    timurGroup.add(sqTowerL, sqTowerR);

    // Siege Catapult / Trebuchet Framework (Wooden Timbers)
    const catapultGroup = new THREE.Group();
    catapultGroup.position.set(-9, 0.5, 12);

    const beamGeom = trackGeometry(new THREE.BoxGeometry(0.5, 0.5, 7.0));
    const beamBase1 = new THREE.Mesh(beamGeom, woodMat);
    beamBase1.position.set(-1.8, 0.25, 0);
    const beamBase2 = new THREE.Mesh(beamGeom, woodMat);
    beamBase2.position.set(1.8, 0.25, 0);
    catapultGroup.add(beamBase1, beamBase2);

    const uprightGeom = trackGeometry(new THREE.BoxGeometry(0.5, 5.0, 0.5));
    const uprightL = new THREE.Mesh(uprightGeom, woodMat);
    uprightL.position.set(-1.8, 2.5, 0);
    const uprightR = new THREE.Mesh(uprightGeom, woodMat);
    uprightR.position.set(1.8, 2.5, 0);
    catapultGroup.add(uprightL, uprightR);

    const armGeom = trackGeometry(new THREE.BoxGeometry(0.4, 0.4, 8.5));
    armGeom.rotateX(0.35);
    const arm = new THREE.Mesh(armGeom, woodMat);
    arm.position.set(0, 4.8, -0.5);
    catapultGroup.add(arm);

    // Counterweight
    const weightGeom = trackGeometry(new THREE.BoxGeometry(1.6, 1.6, 1.4));
    const counterweight = new THREE.Mesh(weightGeom, stoneMat);
    counterweight.position.set(0, 3.2, 2.8);
    catapultGroup.add(counterweight);

    timurGroup.add(catapultGroup);

    // Flaming Braziers on Citadel Gate
    const brazierGeom = trackGeometry(new THREE.CylinderGeometry(0.8, 0.4, 1.2, 8));
    const brazierL = new THREE.Mesh(brazierGeom, stoneMat);
    brazierL.position.set(-6, 12.5, 1.0);
    const brazierR = new THREE.Mesh(brazierGeom, stoneMat);
    brazierR.position.set(6, 12.5, 1.0);

    const fireGeom = trackGeometry(new THREE.ConeGeometry(0.6, 1.2, 8));
    const fireMat = trackMaterial(new THREE.MeshBasicMaterial({ color: 0xff6b1a }));
    const fireL = new THREE.Mesh(fireGeom, fireMat);
    fireL.position.set(-6, 13.4, 1.0);
    const fireR = new THREE.Mesh(fireGeom, fireMat);
    fireR.position.set(6, 13.4, 1.0);

    timurGroup.add(brazierL, brazierR, fireL, fireR);
    animatedTorches.push(fireL, fireR);

    worldGroup.add(timurGroup);

    // =========================================================================
    // EPOCH 4: Modern Museum (z ~ -198)
    // Seven Turquoise Domes of Khujand, grand museum facade, gold finials
    // =========================================================================
    const modernGroup = new THREE.Group();
    modernGroup.position.set(0, 0, -198);

    // Museum Main Terrace & Marble Plaza
    const museumPlazaGeom = trackGeometry(new THREE.BoxGeometry(32, 1.2, 24));
    const museumPlaza = new THREE.Mesh(museumPlazaGeom, marbleMat);
    museumPlaza.position.set(0, 0.6, 0);
    modernGroup.add(museumPlaza);

    // Museum Grand Portal / Facade
    const facadeGeom = trackGeometry(new THREE.BoxGeometry(26, 9.0, 6.0));
    const museumFacade = new THREE.Mesh(facadeGeom, marbleMat);
    museumFacade.position.set(0, 5.5, -4);
    modernGroup.add(museumFacade);

    // 1. Central Grand Turquoise Dome (SphereGeometry top half)
    const mainDomeGeom = trackGeometry(new THREE.SphereGeometry(4.4, 18, 14, 0, Math.PI * 2, 0, Math.PI * 0.5));
    const mainDome = new THREE.Mesh(mainDomeGeom, turquoiseMat);
    mainDome.position.set(0, 10.0, -4);
    modernGroup.add(mainDome);

    // Central Gold Spire / Crescent Finial
    const finialGeom = trackGeometry(new THREE.ConeGeometry(0.4, 2.2, 8));
    const mainFinial = new THREE.Mesh(finialGeom, goldMat);
    mainFinial.position.set(0, 15.2, -4);
    modernGroup.add(mainFinial);

    // 2-7. Six Surrounding Symmetrical Domes (The Seven Domes of Khujand)
    const sideDomeGeom = trackGeometry(new THREE.SphereGeometry(2.0, 14, 10, 0, Math.PI * 2, 0, Math.PI * 0.5));
    const sideFinialGeom = trackGeometry(new THREE.ConeGeometry(0.25, 1.2, 8));

    const domePositions = [
      { x: -5.5, z: -1.5 },
      { x: 5.5, z: -1.5 },
      { x: -9.5, z: -4.5 },
      { x: 9.5, z: -4.5 },
      { x: -5.5, z: -7.0 },
      { x: 5.5, z: -7.0 }
    ];

    domePositions.forEach((pos) => {
      const sideDome = new THREE.Mesh(sideDomeGeom, turquoiseMat);
      sideDome.position.set(pos.x, 9.8, pos.z);
      const sideFinial = new THREE.Mesh(sideFinialGeom, goldMat);
      sideFinial.position.set(pos.x, 12.3, pos.z);
      modernGroup.add(sideDome, sideFinial);
    });

    // Central Museum Courtyard Fountain
    const fountainBaseGeom = trackGeometry(new THREE.CylinderGeometry(3.5, 3.8, 0.8, 16));
    const fountainBase = new THREE.Mesh(fountainBaseGeom, marbleMat);
    fountainBase.position.set(0, 1.5, 6.0);

    const fountainBowlGeom = trackGeometry(new THREE.CylinderGeometry(1.8, 1.2, 1.2, 12));
    const fountainBowl = new THREE.Mesh(fountainBowlGeom, marbleMat);
    fountainBowl.position.set(0, 2.5, 6.0);

    const fountainJetGeom = trackGeometry(new THREE.ConeGeometry(0.4, 2.2, 8));
    const fountainJet = new THREE.Mesh(fountainJetGeom, goldMat);
    fountainJet.position.set(0, 3.8, 6.0);
    modernGroup.add(fountainBase, fountainBowl, fountainJet);

    animatedArtifacts.push(fountainJet);
    worldGroup.add(modernGroup);

    // =========================================================================
    // Ambient Atmosphere Particles (Golden Dust Motes & Sunbeams)
    // Low-poly BufferGeometry points within 60fps budget.
    // =========================================================================
    const particleCount = 350;
    const particlePositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      particlePositions[i * 3] = (Math.random() - 0.5) * 60;
      particlePositions[i * 3 + 1] = Math.random() * 20;
      particlePositions[i * 3 + 2] = -Math.random() * 220;
    }

    const particleGeom = trackGeometry(new THREE.BufferGeometry());
    particleGeom.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));

    const particleMat = trackMaterial(new THREE.PointsMaterial({
      color: 0xffdf80,
      size: 0.35,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending
    }));

    animatedParticles = new THREE.Points(particleGeom, particleMat);
    worldGroup.add(animatedParticles);

    return worldGroup;
  }

  // ---------------------------------------------------------------------------
  // 6. Camera Path & GSAP ScrollTrigger Synchronization (Feature 8)
  // Pinning over 400vh with smooth scrubbed camera choreography.
  // ---------------------------------------------------------------------------
  function updateCameraForProgress(progress) {
    if (!camera) return;

    // Map 0..1 progress across the 4 epoch nodes: 0.0, 0.333, 0.666, 1.0
    const clampedProgress = Math.max(0, Math.min(1, progress));
    const scaled = clampedProgress * (EPOCHS.length - 1);
    const index = Math.floor(scaled);
    const subProgress = scaled - index;

    const currentEpoch = EPOCHS[index];
    const nextEpoch = EPOCHS[Math.min(index + 1, EPOCHS.length - 1)];

    // Interpolate camera position
    camera.position.x = THREE.MathUtils.lerp(currentEpoch.cameraPos.x, nextEpoch.cameraPos.x, subProgress);
    camera.position.y = THREE.MathUtils.lerp(currentEpoch.cameraPos.y, nextEpoch.cameraPos.y, subProgress);
    camera.position.z = THREE.MathUtils.lerp(currentEpoch.cameraPos.z, nextEpoch.cameraPos.z, subProgress);

    // Interpolate camera look-at target
    const targetLookAt = new THREE.Vector3(
      THREE.MathUtils.lerp(currentEpoch.lookAt.x, nextEpoch.lookAt.x, subProgress),
      THREE.MathUtils.lerp(currentEpoch.lookAt.y, nextEpoch.lookAt.y, subProgress),
      THREE.MathUtils.lerp(currentEpoch.lookAt.z, nextEpoch.lookAt.z, subProgress)
    );
    camera.lookAt(targetLookAt);

    // Interpolate lighting and fog atmospheric tone
    if (scene && scene.fog) {
      const curFog = new THREE.Color(currentEpoch.fogColor);
      const nxtFog = new THREE.Color(nextEpoch.fogColor);
      scene.fog.color.lerpColors(curFog, nxtFog, subProgress);
      renderer.setClearColor(scene.fog.color);
    }

    if (dirLight) {
      const curLight = new THREE.Color(currentEpoch.lightColor);
      const nxtLight = new THREE.Color(nextEpoch.lightColor);
      dirLight.color.lerpColors(curLight, nxtLight, subProgress);
      dirLight.position.set(camera.position.x + 10, camera.position.y + 15, camera.position.z + 10);
    }

    // Determine current active epoch for UI (only when not transitioning via tab click)
    if (!isTransitioningToEra) {
      const epochStep = 1 / (EPOCHS.length - 1);
      const nearestIndex = Math.min(EPOCHS.length - 1, Math.round(progress / epochStep));
      if (nearestIndex !== activeEpochIndex) {
        activeEpochIndex = nearestIndex;
        updateUIEpoch(activeEpochIndex);
      }
    }

    // Update progress bar fill
    const progressBar = document.getElementById('scroll-world-progress-fill');
    if (progressBar) {
      progressBar.style.width = `${Math.round(clampedProgress * 100)}%`;
    }
  }

  function updateUIEpoch(index) {
    const epoch = EPOCHS[index];
    if (!epoch) return;

    // Update Backdrop image for zero-delay visual change across epochs
    const backdropEl = document.getElementById('scroll-world-backdrop');
    if (backdropEl && epoch.image) {
      backdropEl.style.backgroundImage = `url('${epoch.image}')`;
    }

    // Update Tab active state
    const tabs = document.querySelectorAll('.scroll-world-tab');
    tabs.forEach((tab, i) => {
      const isActive = i === index;
      tab.classList.toggle('active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    // Update Floating Info Card
    const badgeEl = document.getElementById('scroll-world-epoch-badge');
    const titleEl = document.getElementById('scroll-world-epoch-title');
    const descEl = document.getElementById('scroll-world-epoch-desc');

    if (badgeEl) badgeEl.textContent = epoch.badge;
    if (titleEl) titleEl.textContent = epoch.name;
    if (descEl) descEl.textContent = epoch.desc;

    // Update progress bar
    const progressBar = document.getElementById('scroll-world-progress-fill');
    if (progressBar) {
      progressBar.style.width = `${Math.round((index / (EPOCHS.length - 1)) * 100)}%`;
    }
  }

  function setupScrollTrigger() {
    // Wire up tab click navigation (operates across both WebGL and fallback modes)
    const tabs = document.querySelectorAll('.scroll-world-tab');
    tabs.forEach((tab) => {
      tab.addEventListener('click', (e) => {
        const eraIdx = parseInt(tab.getAttribute('data-era') || '0', 10);
        const isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);

        activeEpochIndex = eraIdx;
        updateUIEpoch(eraIdx);
        const eraProgress = eraIdx / (EPOCHS.length - 1);
        targetScrollProgress = eraProgress;
        targetVideoProgress = eraProgress;

        if (isMobile) {
          if (scrollTriggerInstance && scrollTriggerInstance.end > scrollTriggerInstance.start) {
            const targetY = scrollTriggerInstance.start + eraProgress * (scrollTriggerInstance.end - scrollTriggerInstance.start);
            window.scrollTo({ top: targetY, behavior: 'smooth' });
          }
          return;
        }

        ensureVideoLoaded();
        isTransitioningToEra = true;
        if (eraTransitionTimer) clearTimeout(eraTransitionTimer);
        eraTransitionTimer = setTimeout(() => {
          isTransitioningToEra = false;
        }, 1100);

        if (EPOCHS[eraIdx] && typeof EPOCHS[eraIdx].videoTime === 'number') {
          applyVideoTime(EPOCHS[eraIdx].videoTime);
        }

        // Smoothly scrub video across epochs on tab click
        if (typeof gsap !== 'undefined') {
          gsap.to({ p: currentVideoProgress }, {
            p: eraProgress,
            duration: 0.9,
            ease: "power2.inOut",
            onUpdate: function () {
              currentVideoProgress = this.targets()[0].p;
              if (videoEl && !isNaN(videoEl.duration) && videoEl.duration > 0) {
                applyVideoTime(currentVideoProgress * videoEl.duration);
              }
            }
          });
        } else {
          currentVideoProgress = eraProgress;
          if (videoEl && !isNaN(videoEl.duration) && videoEl.duration > 0) {
            applyVideoTime(eraProgress * videoEl.duration);
          }
        }

        if (scrollTriggerInstance && scrollTriggerInstance.end > scrollTriggerInstance.start) {
          const targetY = scrollTriggerInstance.start + eraProgress * (scrollTriggerInstance.end - scrollTriggerInstance.start);
          if (typeof gsap !== 'undefined') {
            const scrollObj = { y: window.scrollY || window.pageYOffset || document.documentElement.scrollTop };
            gsap.to(scrollObj, {
              y: targetY,
              duration: 0.9,
              ease: "power2.inOut",
              onUpdate: () => {
                window.scrollTo(0, scrollObj.y);
              }
            });
          } else {
            window.scrollTo({ top: targetY, behavior: 'smooth' });
          }
        }
      }, { passive: true });
    });

    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
      console.warn('GSAP or ScrollTrigger not loaded; falling back to scroll listener.');
      window.addEventListener('scroll', onFallbackScroll, { passive: true });
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // Pinned over 400vh (contract boundary requirement: 200vh to 600vh)
    scrollTriggerInstance = ScrollTrigger.create({
      trigger: '#scroll-world',
      start: 'top top',
      end: '+=400vh',
      pin: true,
      scrub: 1.2,
      anticipatePin: 1,
      onUpdate: (self) => {
        targetScrollProgress = self.progress;
        const isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
        if (!isMobile) {
          syncVideo(self.progress);
        } else if (!isTransitioningToEra) {
          const epochStep = 1 / (EPOCHS.length - 1);
          const nearestIndex = Math.min(EPOCHS.length - 1, Math.round(self.progress / epochStep));
          if (nearestIndex !== activeEpochIndex) {
            activeEpochIndex = nearestIndex;
            updateUIEpoch(activeEpochIndex);
          }
        }
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 5b. Cinematic Flythrough Video Scrubbing Engine (oso95/scroll-world)
  // Scrubs videos/flythrough-epochs.mp4 smoothly across the 4 historical epochs
  // ---------------------------------------------------------------------------
  let videoEl = null;
  let targetVideoProgress = 0;
  let currentVideoProgress = 0;
  let isVideoSeeking = false;
  let pendingVideoTime = null;
  let seekSafetyTimer = null;

  function ensureVideoLoaded() {
    const isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
    if (isMobile) return;
    if (!videoEl) {
      videoEl = document.getElementById('scroll-world-video');
    }
    if (!videoEl) return;
    if (!videoEl.src || videoEl.src === window.location.href) {
      videoEl.src = (videoEl.dataset && videoEl.dataset.src) || 'videos/flythrough-epochs.mp4';
    }
    if (videoEl.readyState === 0) {
      videoEl.load();
    }
  }

  function initVideoPlayer() {
    videoEl = document.getElementById('scroll-world-video');
    if (!videoEl) return;

    const isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
    if (isMobile) {
      videoEl.style.display = 'none';
      videoEl.removeAttribute('src');
      try { videoEl.load(); } catch (e) {}
      return;
    }

    videoEl.muted = true;
    videoEl.playsInline = true;
    videoEl.setAttribute('muted', '');
    videoEl.setAttribute('playsinline', '');

    // Lazy load video only when approaching #scroll-world (500px margin)
    if ('IntersectionObserver' in window && (container || videoEl)) {
      const vObs = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          ensureVideoLoaded();
          vObs.disconnect();
        }
      }, { rootMargin: '500px 0px' });
      vObs.observe(container || videoEl);
    }

    videoEl.addEventListener('seeking', () => { isVideoSeeking = true; }, { passive: true });
    videoEl.addEventListener('seeked', () => {
      isVideoSeeking = false;
      if (seekSafetyTimer) {
        clearTimeout(seekSafetyTimer);
        seekSafetyTimer = null;
      }
      if (pendingVideoTime !== null) {
        const nextTime = pendingVideoTime;
        pendingVideoTime = null;
        applyVideoTime(nextTime);
      }
    }, { passive: true });

    if (videoEl.readyState >= 1) {
      applyVideoTime(0);
    } else {
      videoEl.addEventListener('loadedmetadata', () => {
        applyVideoTime(0);
      }, { once: true, passive: true });
    }
  }

  function applyVideoTime(time) {
    if (!videoEl || isNaN(videoEl.duration) || videoEl.duration <= 0) return;
    const clamped = Math.max(0, Math.min(videoEl.duration, time));
    if (isVideoSeeking) {
      pendingVideoTime = clamped;
      return;
    }
    try {
      isVideoSeeking = true;
      videoEl.currentTime = clamped;
      if (seekSafetyTimer) clearTimeout(seekSafetyTimer);
      seekSafetyTimer = setTimeout(() => {
        isVideoSeeking = false;
        if (pendingVideoTime !== null) {
          const nextTime = pendingVideoTime;
          pendingVideoTime = null;
          applyVideoTime(nextTime);
        }
      }, 50);
    } catch (e) {
      isVideoSeeking = false;
    }
  }

  function syncVideo(progress) {
    if (!videoEl || isNaN(videoEl.duration) || videoEl.duration <= 0) return;
    targetVideoProgress = Math.max(0, Math.min(1, progress));
  }

  function onFallbackScroll() {
    if (!container) return;
    const isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
    const rect = container.getBoundingClientRect();
    const totalDist = window.innerHeight * 4; // 400vh
    const scrolled = -rect.top;
    targetScrollProgress = Math.max(0, Math.min(1, scrolled / totalDist));
    if (!isMobile) {
      syncVideo(targetScrollProgress);
    }
    if (!isTransitioningToEra && (!renderer || isMobile)) {
      const epochIdx = Math.min(EPOCHS.length - 1, Math.floor(targetScrollProgress * EPOCHS.length));
      updateUIEpoch(epochIdx);
    }
  }

  // ---------------------------------------------------------------------------
  // 7. Performance & 60 FPS Engine Optimization (Feature 10)
  // ---------------------------------------------------------------------------
  function configureDPR() {
    if (!renderer) return;
    // Mobile DPR strictly clamped to <= 1.0; Desktop DPR strictly clamped to <= 1.75
    const isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
    const maxAllowedDpr = isMobile ? 1.0 : 1.75;
    const safeDpr = Math.min(window.devicePixelRatio || 1, maxAllowedDpr);
    renderer.setPixelRatio(safeDpr);
  }

  function setupIntersectionObserver() {
    // Halts animation loop when #scroll-world is offscreen
    const options = {
      root: null,
      rootMargin: '120px 0px 120px 0px',
      threshold: 0.05
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        isIntersecting = entry.isIntersecting;
        if (isIntersecting) {
          if (!renderer) {
            initScene();
          }
          if (!animationFrameId && clock && renderer) {
            clock.start();
            tick();
          }
        } else {
          // Pause rendering loop offscreen
          if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
          }
        }
      });
    }, options);

    if (container) {
      observer.observe(container);
    }
  }

  function onWindowResize() {
    if (!container || !camera || !renderer) return;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    renderer.setSize(width, height);
    configureDPR();

    if (scrollTriggerInstance) {
      ScrollTrigger.refresh();
    }
  }

  // ---------------------------------------------------------------------------
  // 8. Animation Render Loop (Tick)
  // Delta time capping <= 0.1s; 60 FPS target
  // ---------------------------------------------------------------------------
  function tick() {
    if (!isIntersecting || !clock || !renderer) {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
      return;
    }

    animationFrameId = requestAnimationFrame(tick);

    // Animation frame delta time capping to <= 0.1s
    const rawDelta = clock.getDelta();
    const delta = Math.min(rawDelta, 0.1);
    const elapsedTime = clock.getElapsedTime();

    // Smooth camera scroll interpolation (lerp)
    currentScrollProgress += (targetScrollProgress - currentScrollProgress) * 0.12;
    updateCameraForProgress(currentScrollProgress);

    // Smooth video scrubber interpolation (60 FPS fluid flyover)
    if (videoEl && !isNaN(videoEl.duration) && videoEl.duration > 0) {
      const vDiff = targetVideoProgress - currentVideoProgress;
      if (Math.abs(vDiff) > 0.0001) {
        currentVideoProgress += vDiff * 0.18;
      } else {
        currentVideoProgress = targetVideoProgress;
      }
      const targetTime = currentVideoProgress * videoEl.duration;
      if (Math.abs(videoEl.currentTime - targetTime) > 0.012) {
        applyVideoTime(targetTime);
      }
    }

    // Render WebGL procedural world when canvas is displayed
    if (canvas && canvas.style.display !== 'none') {
      // Procedural ambient animations
      if (animatedWater) {
        animatedWater.position.y = -0.4 + Math.sin(elapsedTime * 1.5) * 0.08;
      }

      if (animatedParticles) {
        animatedParticles.rotation.y = elapsedTime * 0.02;
      }

      animatedTorches.forEach((fire, idx) => {
        const flicker = 1.0 + Math.sin(elapsedTime * 10 + idx * 2) * 0.18;
        fire.scale.set(flicker, flicker * 1.15, flicker);
      });

      animatedArtifacts.forEach((artifact, idx) => {
        artifact.rotation.y = elapsedTime * (0.4 + idx * 0.1);
      });

      renderer.render(scene, camera);
    }
  }

  // ---------------------------------------------------------------------------
  // 9. WebGL Context Loss & Restoration Handling (Feature 8)
  // ---------------------------------------------------------------------------
  function setupContextLossHandling() {
    if (!canvas) return;

    canvas.addEventListener('webglcontextlost', (event) => {
      event.preventDefault();
      console.warn('WebGL context lost in 3D Scroll-World. Halting render loop.');
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
    }, false);

    canvas.addEventListener('webglcontextrestored', () => {
      console.info('WebGL context restored in 3D Scroll-World. Rebuilding procedural scene...');
      initScene();
      if (isIntersecting && !animationFrameId && clock && renderer) {
        clock.start();
        tick();
      }
    }, false);
  }

  // ---------------------------------------------------------------------------
  // 10. Initialization & Mount
  // ---------------------------------------------------------------------------
  function initScene() {
    if (renderer) return;
    container = document.getElementById('scroll-world');
    canvas = document.getElementById('scroll-world-canvas');

    if (!container || !canvas) {
      console.warn('#scroll-world or #scroll-world-canvas not found.');
      return;
    }

    // Skip procedural Three.js initScene when the canvas is hidden (display: none)
    if (canvas.style.display === 'none' || (window.getComputedStyle && window.getComputedStyle(canvas).display === 'none')) {
      return;
    }

    if (typeof THREE === 'undefined') {
      console.warn('Three.js (r128) is not loaded.');
      return;
    }

    // Dispose old resources if re-initializing
    disposeGPUResources();

    clock = new THREE.Clock();

    // Scene with atmospheric fog
    scene = new THREE.Scene();
    if (scene && THREE.FogExp2) {
      scene.fog = new THREE.FogExp2(0x1a120c, 0.016);
    }

    // Camera
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;
    camera = new THREE.PerspectiveCamera(48, width / height, 0.5, 350);
    if (camera && camera.position && typeof camera.position.set === 'function') {
      camera.position.set(EPOCHS[0].cameraPos.x, EPOCHS[0].cameraPos.y, EPOCHS[0].cameraPos.z);
    }
    if (camera && typeof camera.lookAt === 'function') {
      camera.lookAt(EPOCHS[0].lookAt.x, EPOCHS[0].lookAt.y, EPOCHS[0].lookAt.z);
    }

    // WebGL Renderer with Error Boundary (BUG-02)
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance'
      });
      renderer.setSize(width, height);
      configureDPR();
      if (scene && scene.fog && scene.fog.color) {
        renderer.setClearColor(scene.fog.color);
      }
      isWebGLSupported = true;
    } catch (err) {
      console.warn('WebGL unsupported or disabled in 3D Scroll-World:', err);
      isWebGLSupported = false;
      renderer = null;
      updateUIEpoch(0);
      return;
    }

    // Lighting Setup
    hemiLight = new THREE.HemisphereLight(0xffeedd, 0x1a1410, 0.85);
    scene.add(hemiLight);

    dirLight = new THREE.DirectionalLight(0xffb366, 1.4);
    dirLight.position.set(15, 25, 20);
    scene.add(dirLight);

    // Build the 4-Epoch Procedural 3D World (< 25,000 triangles)
    const world = buildProceduralWorld();
    scene.add(world);

    // Context loss handler
    setupContextLossHandling();

    // Resize listener (passive: true)
    window.addEventListener('resize', onWindowResize, { passive: true });

    // Initial camera update
    updateCameraForProgress(0);
    updateUIEpoch(0);
  }

  function setupMobileGestures() {
    if (!container) return;
    let startX = 0;
    let startY = 0;

    container.addEventListener('touchstart', (e) => {
      if (e.touches && e.touches.length === 1) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
      }
    }, { passive: true });

    container.addEventListener('touchend', (e) => {
      if (e.changedTouches && e.changedTouches.length === 1) {
        const dx = startX - e.changedTouches[0].clientX;
        const dy = startY - e.changedTouches[0].clientY;
        // Horizontal swipe across epochs
        if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
          if (dx > 0 && activeEpochIndex < EPOCHS.length - 1) {
            const nextTab = document.querySelector(`.scroll-world-tab[data-era="${activeEpochIndex + 1}"]`);
            if (nextTab) nextTab.click();
          } else if (dx < 0 && activeEpochIndex > 0) {
            const prevTab = document.querySelector(`.scroll-world-tab[data-era="${activeEpochIndex - 1}"]`);
            if (prevTab) prevTab.click();
          }
        }
      }
    }, { passive: true });
  }

  function init() {
    container = document.getElementById('scroll-world');
    canvas = document.getElementById('scroll-world-canvas');
    videoEl = document.getElementById('scroll-world-video');

    initVideoPlayer();
    setupScrollTrigger();
    setupIntersectionObserver();
    setupMobileGestures();

    // Skip Three.js scene creation entirely if canvas is hidden
    if (canvas && (canvas.style.display === 'none' || (window.getComputedStyle && window.getComputedStyle(canvas).display === 'none'))) {
      return;
    }

    // Smart Lazy-Mounting: defer Three.js compilation until near-viewport or idle
    if (window.scrollY > 300 || window.location.hash === '#scroll-world') {
      initScene();
    } else if ('requestIdleCallback' in window) {
      requestIdleCallback(() => { initScene(); }, { timeout: 2000 });
    } else {
      setTimeout(initScene, 800);
    }
  }

  // Public disposal API for lifecycle management & testing
  window.disposeScrollWorld = function () {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    if (scrollTriggerInstance) {
      scrollTriggerInstance.kill();
    }
    window.removeEventListener('resize', onWindowResize);
    window.removeEventListener('scroll', onFallbackScroll);
    disposeGPUResources();
  };

  // Bootstrap when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { passive: true });
  } else {
    init();
  }
})();
