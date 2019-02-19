import copy
from event_model import DocumentRouter

class DarkSubtractionCallback(DocumentRouter):
    def __init__(self,
                 image_key='pe1_image',
                 primary_stream='primary',
                 dark_stream='dark'):
        """Initializes a dark subtraction callback.

        This will perform dark subtraction and then save to file.

        Parameters
        ----------
        image_key : str (optional)
            The detector image string
        primary_stream : str (optional)
            The primary stream name
        dark_stream : str (optional)
            The dark stream name
        """

        self.pstream = primary_stream
        self.dstream = dark_stream
        self.image_key = image_key
        self.descriptors = {}
        self._last_dark = None
        self._has_started = False

    def start(self, doc):
        if self._has_started:
            raise RuntimeError('Can handle only one run. '
                               'Two start documents found.')
        else:
            self._has_started = True
            return super().start(doc)

    def descriptor(self, doc):
        # Note: we may want to indicate background subtraction
        self.descriptors[doc['uid']] = doc
        return super().descriptor(doc)

    def event_page(self, doc):
        # Note: we may want to update the image key to indicate background
        # subtraction in the outgoing doc.
        stream_name = self.descriptors[doc['descriptor']]['name']
        
        if stream_name not in [self.pstream, self.dstream]:
            return doc
        
        if self.image_key in doc['data']:
            if stream_name == self.dstream:
                self._last_dark = doc['data'][self.image_key][-1]
                # TODO: deal with properly-paged data later
                return doc
            elif stream_name == self.pstream:
                # Actual subtraction is happening here:
                return_doc = copy.deepcopy(doc) 
                dsub_images = [im - self._last_dark
                               for im in return_doc['data'][self.image_key]]

                return_doc['data'][self.image_key] = dsub_images
                return return_doc
            else:
                raise RuntimeError(f'The stream name "{stream_name}" must be '
                                   f'one of {self.pstream} or {self.dstream}')
        else:
            return doc


# Background subtraction callback
# TODO: this needs to be a wrapped RunRouter, figure out later
bgsub_callback = DarkSubtractionCallback(image_key="pe1_image",
                                         primary_stream="primary",
                                         dark_stream="dark")

# TODO: need to attach a callback registry to the run router above
RE.subscribe(bgsub_callback)
