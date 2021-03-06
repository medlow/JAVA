import cv2
import gradio as gr
import numpy as np
import onnxruntime
import requests
from huggingface_hub import hf_hub_download
from PIL import Image


# Get x_scale_factor & y_scale_factor to resize image
def get_scale_factor(im_h, im_w, ref_size=512):

    if max(im_h, im_w) < ref_size or min(im_h, im_w) > ref_size:
        if im_w >= im_h:
            im_rh = ref_size
            im_rw = int(im_w / im_h * ref_size)
        elif im_w < im_h:
            im_rw = ref_size
            im_rh = int(im_h / im_w * ref_size)
    else:
        im_rh = im_h
        im_rw = im_w

    im_rw = im_rw - im_rw % 32
    im_rh = im_rh - im_rh % 32

    x_scale_factor = im_rw / im_w
    y_scale_factor = im_rh / im_h

    return x_scale_factor, y_scale_factor


MODEL_PATH = hf_hub_download('nateraw/background-remover-files', 'modnet.onnx', repo_type='dataset')


def main(image_path, threshold):

    # read image
    im = cv2.imread(image_path)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    # unify image channels to 3
    if len(im.shape) == 2:
        im = im[:, :, None]
    if im.shape[2] == 1:
        im = np.repeat(im, 3, axis=2)
    elif im.shape[2] == 4:
        im = im[:, :, 0:3]

    # normalize values to scale it between -1 to 1
    im = (im - 127.5) / 127.5

    im_h, im_w, im_c = im.shape
    x, y = get_scale_factor(im_h, im_w)

    # resize image
    im = cv2.resize(im, None, fx=x, fy=y, interpolation=cv2.INTER_AREA)

    # prepare input shape
    im = np.transpose(im)
    im = np.swapaxes(im, 1, 2)
    im = np.expand_dims(im, axis=0).astype('float32')

    # Initialize session and get prediction
    session = onnxruntime.InferenceSession(MODEL_PATH, None)
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    result = session.run([output_name], {input_name: im})

    # refine matte
    matte = (np.squeeze(result[0]) * 255).astype('uint8')
    matte = cv2.resize(matte, dsize=(im_w, im_h), interpolation=cv2.INTER_AREA)

    # HACK - Could probably just convert this to PIL instead of writing
    cv2.imwrite('out.png', matte)

    image = Image.open(image_path)
    matte = Image.open('out.png')

    # obtain predicted foreground
    image = np.asarray(image)
    if len(image.shape) == 2:
        image = image[:, :, None]
    if image.shape[2] == 1:
        image = np.repeat(image, 3, axis=2)
    elif image.shape[2] == 4:
        image = image[:, :, 0:3]

    b, g, r = cv2.split(image)

    mask = np.asarray(matte)
    a = np.ones(mask.shape, dtype='uint8') * 255
    alpha_im = cv2.merge([b, g, r, a], 4)

    new_mask = np.stack([mask, mask, mask, mask], axis=2)
    foreground = np.where(new_mask > threshold, alpha_im, bg).astype(np.uint8)

    return Image.fromarray(foreground)


title = "Groupe 12 background remover"
description = "Groupe 12 background remover est un mod??le capable de supprimer l'arri??re-plan d'une image donn??e. Pour l'utiliser, il suffit de t??l??charger votre image, ou de cliquer sur l'un des exemples pour les charger. Pour en savoir plus, cliquez sur les liens ci-dessous.."


url = "https://huggingface.co/datasets/nateraw/background-remover-files/resolve/main/twitter_profile_pic.jpeg"
image = Image.open(requests.get(url, stream=True).raw)
image.save('twitter_profile_pic.jpg')

url = "https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg"
image = Image.open(requests.get(url, stream=True).raw)
image.save('obama.jpg')

interface = gr.Interface(
    fn=main,
    inputs=[
        gr.inputs.Image(type='filepath'),
        gr.inputs.Slider(minimum=0, maximum=250, default=100, step=5, label='Mask Cutoff Threshold'),
    ],
    outputs='image',
    examples=[['twitter_profile_pic.jpg', 120], ['obama.jpg', 155]],
    title=title,
    description=description,
    article=article,
)

if __name__ == '__main__':
    interface.launch(debug=True)
   