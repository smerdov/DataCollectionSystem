package com.flir.flironeexampleapplication;

import android.Manifest;
import android.annotation.TargetApi;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.PorterDuff;
import android.graphics.drawable.Drawable;
import android.media.MediaScannerConnection;
import android.net.Uri;
import android.opengl.GLSurfaceView;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v4.content.PermissionChecker;
import android.util.Log;
import android.view.MotionEvent;
import android.view.OrientationEventListener;
import android.view.ScaleGestureDetector;
import android.view.View;
import android.view.WindowManager;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ToggleButton;

import com.flir.flironeexampleapplication.util.SystemUiHider;
import com.flir.flironesdk.Device;
import com.flir.flironesdk.FlirUsbDevice;
import com.flir.flironesdk.Frame;
import com.flir.flironesdk.FrameProcessor;
import com.flir.flironesdk.LoadedFrame;
import com.flir.flironesdk.RenderedImage;
import com.flir.flironesdk.SimulatedDevice;

import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.lang.reflect.Field;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.lang.*;

/**
 * An example activity and delegate for FLIR One image streaming and device interaction.
 * Based on an example full-screen activity that shows and hides the system UI (i.e.
 * status bar and navigation/system bar) with user interaction.
 *
 * @see SystemUiHider
 * @see Device.Delegate
 * @see FrameProcessor.Delegate
 * @see Device.StreamDelegate
 * @see Device.PowerUpdateDelegate
 */


public class GLPreviewActivity extends Activity implements Device.Delegate, FrameProcessor.Delegate, Device.StreamDelegate, Device.PowerUpdateDelegate{
    GLSurfaceView thermalSurfaceView;
//    private volatile boolean imageCaptureRequested = false;
//    public volatile boolean recordingOn = false;
    private volatile Socket streamSocket = null;
    private boolean chargeCableIsConnected = true;

    private int deviceRotation= 0;
    private OrientationEventListener orientationEventListener;


    private volatile Device flirOneDevice;
    private FrameProcessor frameProcessor;

//    private String lastSavedPath;

    private Device.TuningState currentTuningState = Device.TuningState.Unknown;

    Server background_server = new Server();
    Thread recording_thread = new Thread(background_server);



    // Device Delegate methods

    // Called during device discovery, when a device is connected
    // During this callback, you should save a reference to device
    // You should also set the power update delegate for the device if you have one
    // Go ahead and start frame stream as soon as connected, in this use case
    // Finally we create a frame processor for rendering frames

    public void onDeviceConnected(Device device){
        Log.i("ExampleApp", "Device connected!");
        runOnUiThread(new Runnable() {
                          @Override
                          public void run() {
                              findViewById(R.id.pleaseConnect).setVisibility(View.GONE);
                          }
                      });
        
        flirOneDevice = device;
        flirOneDevice.setPowerUpdateDelegate(this);
        flirOneDevice.startFrameStream(this);

        final ToggleButton chargeCableButton = (ToggleButton)findViewById(R.id.chargeCableToggle);
        if(flirOneDevice instanceof SimulatedDevice){
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    chargeCableButton.setChecked(chargeCableIsConnected);
                    chargeCableButton.setVisibility(View.VISIBLE);
                }
            });
        }else{
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    chargeCableButton.setChecked(chargeCableIsConnected);
                    chargeCableButton.setVisibility(View.INVISIBLE);
                    findViewById(R.id.connect_sim_button).setEnabled(false);

                }
            });
        }

        orientationEventListener.enable();
        recording_thread.start();
    }

    /**
     * Indicate to the user that the device has disconnected
     */
    public void onDeviceDisconnected(Device device){
        Log.i("ExampleApp", "Device disconnected!");

        final ToggleButton chargeCableButton = (ToggleButton)findViewById(R.id.chargeCableToggle);
        final TextView levelTextView = (TextView)findViewById(R.id.batteryLevelTextView);
        final ImageView chargingIndicator = (ImageView)findViewById(R.id.batteryChargeIndicator);
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                findViewById(R.id.pleaseConnect).setVisibility(View.GONE);
                levelTextView.setText("--");
                chargeCableButton.setChecked(chargeCableIsConnected);
                chargeCableButton.setVisibility(View.INVISIBLE);
                chargingIndicator.setVisibility(View.GONE);
                findViewById(R.id.tuningProgressBar).setVisibility(View.GONE);
                findViewById(R.id.tuningTextView).setVisibility(View.GONE);
                findViewById(R.id.connect_sim_button).setEnabled(true);
            }
        });
        flirOneDevice = null;
        orientationEventListener.disable();
    }

    /**
     * If using RenderedImage.ImageType.ThermalRadiometricKelvinImage, you should not rely on
     * the accuracy if tuningState is not Device.TuningState.Tuned
     * @param tuningState
     */
    public void onTuningStateChanged(Device.TuningState tuningState){
        Log.i("ExampleApp", "Tuning state changed changed!");

        currentTuningState = tuningState;
        if (tuningState == Device.TuningState.InProgress){
            runOnUiThread(new Thread(){
                @Override
                public void run() {
                    super.run();
                    findViewById(R.id.tuningProgressBar).setVisibility(View.VISIBLE);
                    findViewById(R.id.tuningTextView).setVisibility(View.VISIBLE);
                }
            });
        }else {
            runOnUiThread(new Thread() {
                @Override
                public void run() {
                    super.run();
                    findViewById(R.id.tuningProgressBar).setVisibility(View.GONE);
                    findViewById(R.id.tuningTextView).setVisibility(View.GONE);
                }
            });
        }
    }

    @Override
    public void onAutomaticTuningChanged(boolean deviceWillTuneAutomatically) {

    }
    private ColorFilter originalChargingIndicatorColor = null;
    @Override
    public void onBatteryChargingStateReceived(final Device.BatteryChargingState batteryChargingState) {
        Log.i("ExampleApp", "Battery charging state received!");

        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                ImageView chargingIndicator = (ImageView)findViewById(R.id.batteryChargeIndicator);
                if (originalChargingIndicatorColor == null){
                    originalChargingIndicatorColor = chargingIndicator.getColorFilter();
                }
                switch (batteryChargingState) {
                    case FAULT:
                    case FAULT_HEAT:
                        chargingIndicator.setColorFilter(Color.RED);
                        chargingIndicator.setVisibility(View.VISIBLE);
                        break;
                    case FAULT_BAD_CHARGER:
                        chargingIndicator.setColorFilter(Color.DKGRAY);
                        chargingIndicator.setVisibility(View.VISIBLE);
                    case MANAGED_CHARGING:
                        chargingIndicator.setColorFilter(originalChargingIndicatorColor);
                        chargingIndicator.setVisibility(View.VISIBLE);
                        break;
                    case NO_CHARGING:
                    default:
                        chargingIndicator.setVisibility(View.GONE);
                        break;
                }
            }
        });
    }
    @Override
    public void onBatteryPercentageReceived(final byte percentage){
        Log.i("ExampleApp", "Battery percentage received!");

        final TextView levelTextView = (TextView)findViewById(R.id.batteryLevelTextView);
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                levelTextView.setText(String.valueOf((int) percentage) + "%");
            }
        });


    }

    // StreamDelegate method
    public void onFrameReceived(Frame frame) {
        Log.v("ExampleApp", "Frame received!");

        if (currentTuningState != Device.TuningState.InProgress){
            frameProcessor.processFrame(frame, FrameProcessor.QueuingOption.CLEAR_QUEUED);
            thermalSurfaceView.requestRender();
        }
    }

    private Bitmap thermalBitmap = null;

    // Frame Processor Delegate method, will be called each time a rendered frame is produced
    public void onFrameProcessed(final RenderedImage renderedImage){
        background_server.setUpImage(renderedImage);

        if (renderedImage.imageType() == RenderedImage.ImageType.ThermalRadiometricKelvinImage){
            // Note: this code is not optimized

            int[] thermalPixels = renderedImage.thermalPixelValues();
            // average the center 9 pixels for the spot meter

            int width = renderedImage.width();
            int height = renderedImage.height();
            int centerPixelIndex = width * (height/2) + (width/2);
            int[] centerPixelIndexes = new int[] {
                    centerPixelIndex, centerPixelIndex-1, centerPixelIndex+1,
                    centerPixelIndex - width,
                    centerPixelIndex - width - 1,
                    centerPixelIndex - width + 1,
                    centerPixelIndex + width,
                    centerPixelIndex + width - 1,
                    centerPixelIndex + width + 1
            };

            double averageTemp = 0;

            for (int i = 0; i < centerPixelIndexes.length; i++){
                // Remember: all primitives are signed, we want the unsigned value,
                // we've used renderedImage.thermalPixelValues() to get unsigned values
                int pixelValue = (thermalPixels[centerPixelIndexes[i]]);
                averageTemp += (((double)pixelValue) - averageTemp) / ((double) i + 1);
            }
            double averageC = (averageTemp / 100) - 273.15;
            NumberFormat numberFormat = NumberFormat.getInstance();
            numberFormat.setMaximumFractionDigits(2);
            numberFormat.setMinimumFractionDigits(2);
            final String spotMeterValue = numberFormat.format(averageC) + "ºC";
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    ((TextView)findViewById(R.id.spotMeterValue)).setText(spotMeterValue);
                }
            });
        }

        /*
        Capture this image if requested.
        */
//        if (this.imageCaptureRequested) {
//
////            imageCaptureRequested = false;
////            final Context context = this;
//
//            background_server.start_recording();
//        }
    }




    /**
     * Whether or not the system UI should be auto-hidden after
     * {@link #AUTO_HIDE_DELAY_MILLIS} milliseconds.
     */
    private static final boolean AUTO_HIDE = true;

    /**
     * If {@link #AUTO_HIDE} is set, the number of milliseconds to wait after
     * user interaction before hiding the system UI.
     */
    private static final int AUTO_HIDE_DELAY_MILLIS = 3000;

    /**
     * If set, will toggle the system UI visibility upon interaction. Otherwise,
     * will show the system UI visibility upon interaction.
     */
    private static final boolean TOGGLE_ON_CLICK = true;

    /**
     * The flags to pass to {@link SystemUiHider#getInstance}.
     */
    private static final int HIDER_FLAGS = SystemUiHider.FLAG_HIDE_NAVIGATION;

    /**
     * The instance of the {@link SystemUiHider} for this activity.
     */
    private SystemUiHider mSystemUiHider;
    public void onTuneClicked(View v){
        if (flirOneDevice != null){
            flirOneDevice.performTuning();
        }

    }
    public void onCaptureRecordingStart(View v){
//        Toast.makeText(this, "Trying to start recording...", Toast.LENGTH_LONG).show();
        if(flirOneDevice != null) {
//            this.imageCaptureRequested = true;
//            this.recordingOn = true;
            if (background_server.recording_on) {
                Toast.makeText(this, "Already recording", Toast.LENGTH_LONG).show();
            } else {
                Toast.makeText(this, "Starting recording...", Toast.LENGTH_LONG).show();
            }

            background_server.start_recording();

            ImageView imgStatus = findViewById(R.id.Status);
            imgStatus.setColorFilter(Color.GREEN, PorterDuff.Mode.MULTIPLY);

        }
    }
    public void onCaptureRecordingStop(View v){
//        if(flirOneDevice != null) {
//            this.recordingOn = false;
        if (background_server.recording_on) {
            Toast.makeText(this, "Stopping recording...", Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(this, "Already stopped", Toast.LENGTH_LONG).show();
        }
        background_server.stop_recording();

        ImageView imgStatus = findViewById(R.id.Status);
        imgStatus.setColorFilter(Color.WHITE, PorterDuff.Mode.MULTIPLY);
//        }
    }

    public void onConnectSimClicked(View v){
        if(flirOneDevice == null){
            try {
                flirOneDevice = new SimulatedDevice(this, this, getResources().openRawResource(R.raw.sampleframes), 10);
                flirOneDevice.setPowerUpdateDelegate(this);
                chargeCableIsConnected = true;
            } catch(Exception ex) {
                flirOneDevice = null;
                Log.w("FLIROneExampleApp", "IO EXCEPTION");
                ex.printStackTrace();
            }
        }else if(flirOneDevice instanceof SimulatedDevice) {
            flirOneDevice.close();
            flirOneDevice = null;
        }
    }

    public void onSimulatedChargeCableToggleClicked(View v){
        if(flirOneDevice instanceof SimulatedDevice){
            chargeCableIsConnected = !chargeCableIsConnected;
            ((SimulatedDevice)flirOneDevice).setChargeCableState(chargeCableIsConnected);
        }
    }
    public void onRotateClicked(View v){
        ToggleButton theSwitch = (ToggleButton)v;
        if (theSwitch.isChecked()){
            frameProcessor.setImageRotation(180.0f);
        }else{
            frameProcessor.setImageRotation(0.0f);
        }
    }
    public void onChangeViewClicked(View v){
        if (frameProcessor == null){
            ((ToggleButton)v).setChecked(false);
            return;
        }
        ListView paletteListView = (ListView)findViewById(R.id.paletteListView);
        ListView imageTypeListView = (ListView)findViewById(R.id.imageTypeListView);
        if (((ToggleButton)v).isChecked()){
            // only show palette list if selected image type is colorized
            paletteListView.setVisibility(View.INVISIBLE);
            for (RenderedImage.ImageType imageType : frameProcessor.getImageTypes()){
                if (imageType.isColorized()) {
                    paletteListView.setVisibility(View.VISIBLE);
                    break;
                }
            }
            imageTypeListView.setVisibility(View.VISIBLE);
            findViewById(R.id.imageTypeListContainer).setVisibility(View.VISIBLE);
        }else{
            findViewById(R.id.imageTypeListContainer).setVisibility(View.GONE);
        }


    }

    public void onImageTypeListViewClicked(View v){
        int index = ((ListView) v).getSelectedItemPosition();
        RenderedImage.ImageType imageType = RenderedImage.ImageType.values()[index];
        frameProcessor.setGLOutputMode(imageType);
        int paletteVisibility = (imageType.isColorized()) ? View.VISIBLE : View.GONE;
        findViewById(R.id.paletteListView).setVisibility(paletteVisibility);
    }

    public void onPaletteListViewClicked(View v){
        RenderedImage.Palette pal = (RenderedImage.Palette )(((ListView)v).getSelectedItem());
        frameProcessor.setImagePalette(pal);
    }

    /**
     * Example method of starting/stopping a frame stream to a host
     * @param v The toggle button pushed
     */
    public void onVividClicked(View v){
        final ToggleButton button = (ToggleButton)v;
        frameProcessor.setVividIrEnabled(button.isChecked());
    }

    @Override
    protected void onStart(){
        super.onStart();
        if (Device.getSupportedDeviceClasses(this).contains(FlirUsbDevice.class)){
            findViewById(R.id.pleaseConnect).setVisibility(View.VISIBLE);
        }
        try {
            Device.startDiscovery(this, this);
        }catch(IllegalStateException e){
            // it's okay if we've already started discovery
        }catch (SecurityException e){
            // On some platforms, we need the user to select the app to give us permisison to the USB device.
            Toast.makeText(this, "Please insert FLIR One and select "+getString(R.string.app_name), Toast.LENGTH_LONG).show();
            // There is likely a cleaner way to recover, but for now, exit the activity and
            // wait for user to follow the instructions;
            finish();
        }
    }

    ScaleGestureDetector mScaleDetector;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_gl_preview);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        final View controlsView = findViewById(R.id.fullscreen_content_controls);
        final View controlsViewTop = findViewById(R.id.fullscreen_content_controls_top);
        final View contentView = findViewById(R.id.fullscreen_content);

        RenderedImage.ImageType defaultImageType = RenderedImage.ImageType.BlendedMSXRGBA8888Image;
        frameProcessor = new FrameProcessor(this, this, EnumSet.of(RenderedImage.ImageType.ThermalRadiometricKelvinImage), true);
        frameProcessor.setGLOutputMode(defaultImageType);

        thermalSurfaceView = (GLSurfaceView) findViewById(R.id.imageView);
        thermalSurfaceView.setPreserveEGLContextOnPause(true);
        thermalSurfaceView.setEGLContextClientVersion(2);
        thermalSurfaceView.setRenderer(frameProcessor);
        thermalSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_WHEN_DIRTY);
        thermalSurfaceView.setDebugFlags(GLSurfaceView.DEBUG_CHECK_GL_ERROR | GLSurfaceView.DEBUG_LOG_GL_CALLS);


        final String[] imageTypeNames = new String[]{ "Visible", "Thermal", "MSX" };
        final RenderedImage.ImageType[] imageTypeValues = new RenderedImage.ImageType[]{
                RenderedImage.ImageType.VisibleAlignedRGBA8888Image,
                RenderedImage.ImageType.ThermalRGBA8888Image,
                RenderedImage.ImageType.BlendedMSXRGBA8888Image,
        };

        ListView imageTypeListView = ((ListView)findViewById(R.id.imageTypeListView));
        imageTypeListView.setAdapter(new ArrayAdapter<>(this,R.layout.emptytextview,imageTypeNames));
        imageTypeListView.setSelection(defaultImageType.ordinal());
        imageTypeListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                if (frameProcessor != null) {
                    RenderedImage.ImageType imageType = imageTypeValues[position];
                    frameProcessor.setGLOutputMode(imageType);
                    if (imageType.isColorized()){
                        findViewById(R.id.paletteListView).setVisibility(View.VISIBLE);
                    }else{
                        findViewById(R.id.paletteListView).setVisibility(View.INVISIBLE);
                    }
                }
            }
        });
        imageTypeListView.setDivider(null);

        // Palette List View Setup
        ListView paletteListView = ((ListView)findViewById(R.id.paletteListView));
        paletteListView.setDivider(null);
        paletteListView.setAdapter(new ArrayAdapter<>(this, R.layout.emptytextview, RenderedImage.Palette.values()));
        paletteListView.setSelection(frameProcessor.getImagePalette().ordinal());
        paletteListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                if (frameProcessor != null){
                    frameProcessor.setImagePalette(RenderedImage.Palette.values()[position]);
                }
            }
        });
        // Set up an instance of SystemUiHider to control the system UI for
        // this activity.

        mSystemUiHider = SystemUiHider.getInstance(this, contentView, HIDER_FLAGS);
        mSystemUiHider.setup();

        mSystemUiHider
                .setOnVisibilityChangeListener(new SystemUiHider.OnVisibilityChangeListener() {
                    // Cached values.
                    int mControlsHeight;
                    int mShortAnimTime;

                    @Override
                    @TargetApi(Build.VERSION_CODES.HONEYCOMB_MR2)
                    public void onVisibilityChange(boolean visible) {
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.HONEYCOMB_MR2) {
                            // If the ViewPropertyAnimator API is available
                            // (Honeycomb MR2 and later), use it to animate the
                            // in-layout UI controls at the bottom of the
                            // screen.
                            if (mControlsHeight == 0) {
                                mControlsHeight = controlsView.getHeight();
                            }
                            if (mShortAnimTime == 0) {
                                mShortAnimTime = getResources().getInteger(
                                        android.R.integer.config_shortAnimTime);
                            }
                            controlsView.animate()
                                    .translationY(visible ? 0 : mControlsHeight)
                                    .setDuration(mShortAnimTime);
                            controlsViewTop.animate().translationY(visible ? 0 : -1 * mControlsHeight).setDuration(mShortAnimTime);
                        } else {
                            // If the ViewPropertyAnimator APIs aren't
                            // available, simply show or hide the in-layout UI
                            // controls.
                            controlsView.setVisibility(visible ? View.VISIBLE : View.GONE);
                            controlsViewTop.setVisibility(visible ? View.VISIBLE : View.GONE);
                        }

                        if (visible && !((ToggleButton)findViewById(R.id.change_view_button)).isChecked() && AUTO_HIDE) {
                            // Schedule a hide().
                            delayedHide(AUTO_HIDE_DELAY_MILLIS);
                        }
                    }
                });

        // Set up the user interaction to manually show or hide the system UI.
        contentView.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                if (TOGGLE_ON_CLICK) {
                    mSystemUiHider.toggle();
                } else {
                    mSystemUiHider.show();
                }
            }
        });

        // Upon interacting with UI controls, delay any scheduled hide()
        // operations to prevent the jarring behavior of controls going away
        // while interacting with the UI.
        findViewById(R.id.change_view_button).setOnTouchListener(mDelayHideTouchListener);


        orientationEventListener = new OrientationEventListener(this) {
            @Override
            public void onOrientationChanged(int orientation) {
                deviceRotation = orientation;
            }
        };
        mScaleDetector = new ScaleGestureDetector(this, new ScaleGestureDetector.OnScaleGestureListener() {
            @Override
            public void onScaleEnd(ScaleGestureDetector detector) {
            }
            @Override
            public boolean onScaleBegin(ScaleGestureDetector detector) {
                return true;
            }
            @Override
            public boolean onScale(ScaleGestureDetector detector) {
                Log.d("ZOOM", "zoom ongoing, scale: " + detector.getScaleFactor());
                frameProcessor.setMSXDistance(detector.getScaleFactor());
                return false;
            }
        });

        findViewById(R.id.fullscreen_content).setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                mScaleDetector.onTouchEvent(event);
                return true;
            }
        });

        // ask for permission?
        String writePermission = Manifest.permission.WRITE_EXTERNAL_STORAGE;
        boolean permissionGranted = false;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            permissionGranted = (ContextCompat.checkSelfPermission(this, writePermission) == PackageManager.PERMISSION_GRANTED);
        }
        else {
            permissionGranted = (PermissionChecker.checkSelfPermission(this, writePermission) == PermissionChecker.PERMISSION_GRANTED);
        }

        if(!permissionGranted) {
            if (ActivityCompat.shouldShowRequestPermissionRationale(this, writePermission)) {
                Toast.makeText(this, "App requires write permission to save photos", Toast.LENGTH_LONG).show();
            }
            else {
                ActivityCompat.requestPermissions(this, new String[]{writePermission}, 0);
            }
        }
    }

    @Override
    public void onPause(){
        super.onPause();

        thermalSurfaceView.onPause();
        if (flirOneDevice != null){
            flirOneDevice.stopFrameStream();
        }
    }
    @Override
    public void onResume(){
        super.onResume();

        thermalSurfaceView.onResume();

        if (flirOneDevice != null){
            flirOneDevice.startFrameStream(this);
        }
    }
    @Override
    public void onStop() {
        // We must unregister our usb receiver, otherwise we will steal events from other apps
        Log.e("PreviewActivity", "onStop, stopping discovery!");
        Device.stopDiscovery();
        flirOneDevice = null;
        super.onStop();
    }

    @Override
    protected void onPostCreate(Bundle savedInstanceState) {
        super.onPostCreate(savedInstanceState);

        // Trigger the initial hide() shortly after the activity has been
        // created, to briefly hint to the user that UI controls
        // are available.
        delayedHide(100);
    }


    /**
     * Touch listener to use for in-layout UI controls to delay hiding the
     * system UI. This is to prevent the jarring behavior of controls going away
     * while interacting with activity UI.
     */
    View.OnTouchListener mDelayHideTouchListener = new View.OnTouchListener() {
        @Override
        public boolean onTouch(View view, MotionEvent motionEvent) {
            if (AUTO_HIDE) {
                delayedHide(AUTO_HIDE_DELAY_MILLIS);
            }
            return false;
        }
    };

    Handler mHideHandler = new Handler();
    Runnable mHideRunnable = new Runnable() {
        @Override
        public void run() {
            mSystemUiHider.hide();
        }
    };

    /**
     * Schedules a call to hide() in [delay] milliseconds, canceling any
     * previously scheduled calls.
     */
    private void delayedHide(int delayMillis) {
        mHideHandler.removeCallbacks(mHideRunnable);
        mHideHandler.postDelayed(mHideRunnable, delayMillis);
    }
}

class Server implements Runnable{
    public volatile boolean recording_on = false;
    private RenderedImage renderedImage;
    GLPreviewActivity parent;
    private int idleSleepTime = 1000;
    private int recordingPeriod = 5000;

    public void setUpImage(final RenderedImage renderedImageExternal){
        renderedImage = renderedImageExternal;
    }

    public void setUpThis(final GLPreviewActivity parent_instance){
        parent = parent_instance;
    }


    public void run() {
        while (true) {
//        (this.recording_on) {
            if (!this.recording_on){
                try{
//                    Toast.makeText(parent, "Sleeping...", Toast.LENGTH_LONG).show();
                    Thread.sleep(idleSleepTime);
                } catch (Exception e) {
                    System.out.println(e);
                }

                continue;
            }

//            Toast.makeText(parent, "Recording...", Toast.LENGTH_LONG).show();

            String lastSavedPath;
            String path = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES).toString();
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd-HH-mm-ss", Locale.getDefault());


            String formatedDate = sdf.format(new Date());
            String fileName = "thermal_data_" + formatedDate + ".csv";

//                    public static void write (String fileName, int[]x) throws IOException{
            try {
                int[] thermalPixels = renderedImage.thermalPixelValues();
                lastSavedPath = path + "/" + fileName;
                BufferedWriter outputWriter = null;
                outputWriter = new BufferedWriter(new FileWriter(lastSavedPath));
                NumberFormat numberFormat = NumberFormat.getInstance();
                numberFormat.setMaximumFractionDigits(2);
                numberFormat.setMinimumFractionDigits(2);

//                        for (int i = 0; i < thermalPixels.length; i++) {
                int step_size = 10;
                int width = renderedImage.width();
                int height = renderedImage.height();

                int n_horizontal_steps = width / step_size;
                int n_vertical_steps = height / step_size;
                char end_of_line_character;

                for (int i = 0; i < thermalPixels.length / (step_size * step_size); i++) {
                    // Maybe:
                    int horizontal_coordinate = (i % n_horizontal_steps) * step_size + step_size / 2;
                    int vertical_coordinate = (i / n_horizontal_steps) * step_size + step_size / 2;
                    int array_index = vertical_coordinate * width + horizontal_coordinate;

                    double valueCelcius = ((double) thermalPixels[array_index] / 100) - 273.15;
                    final String valueCelciusString = numberFormat.format(valueCelcius);
                    if (i % n_horizontal_steps == n_horizontal_steps - 1) {
                        end_of_line_character = '\n';
                    } else {
                        end_of_line_character = ',';
                    }

                    outputWriter.write(valueCelciusString + end_of_line_character);
//                            outputWriter.write(valueCelciusString + ",");
                    // Or:
//                            outputWriter.write(Integer.toString(thermalPixels[i]));
//                            outputWriter.newLine();
                }
                outputWriter.flush();
                outputWriter.close();

                try{
                    Thread.sleep(recordingPeriod);
                } catch (Exception e) {
                    System.out.println(e);
                }

            } catch (Exception e) {
                e.printStackTrace();
            }
        }
//                    }

//                    try{
//                        lastSavedPath = path+ "/" + fileName;
//                        renderedImage.getFrame().save(new File(lastSavedPath), frameProcessor);
//
//                        MediaScannerConnection.scanFile(context,
//                                new String[]{path + "/" + fileName}, null,
//                                new MediaScannerConnection.OnScanCompletedListener() {
//                                    @Override
//                                    public void onScanCompleted(String path, Uri uri) {
//                                        Log.i("ExternalStorage", "Scanned " + path + ":");
//                                        Log.i("ExternalStorage", "-> uri=" + uri);
//                                    }
//
//                                });
//
//                    }catch (Exception e){
//                        e.printStackTrace();
//                    }
    }

    public void stop_recording() {
        recording_on = false;
    }

    public void start_recording() {
        recording_on = true;
    }
}
