add_media = """mutation createMedia($realItemId: Int!, $mediaUrl: String!, $label: String!, $type: String!) {
  createMedia(realItemId: $realItemId, mediaUrl: $mediaUrl, label: $label, type: $type) {
    ok
    media {
      databaseId
    }
  }
}"""

del_media = """mutation delMedia($databaseId: Int!){
  deleteMedia(databaseId: $databaseId) {
    ok
    debug
  }
}"""

upd_media = """mutation updateMedia($databaseId: Int!, $label: String!, $type: String!) {
  updateMedia(databaseId: $databaseId, label: $label, type: $type) {
    ok
    media {
      databaseId
    }
  }
}
"""